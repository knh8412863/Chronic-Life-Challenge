from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.core import config
from app.dtos.pets import (
    PetCatalogItemResponse,
    PetCatalogResponse,
    PetCatalogSummaryResponse,
    PetRecentActivityResponse,
    PetRewardClaimResponse,
    PetRewardTaskResponse,
    VirtualPetCreateRequest,
    VirtualPetCreateResponse,
    VirtualPetNameUpdateRequest,
    VirtualPetNameUpdateResponse,
    VirtualPetResponse,
    VirtualPetStatusResponse,
)
from app.models.challenges import ChallengeCheckin, ChallengeParticipation
from app.models.pets import PetActivityType, PetGrowthStage, PetType, VirtualPet, VirtualPetActivityLog
from app.models.predictions import ActivityLog, ExerciseLog, VitalRecord
from app.models.users import User

DATE_KEY_FORMAT = "%Y%m%d"
_CURRENT_PET_TYPE_UNSET = object()

BASE_REWARD_TASKS = [
    ("VITAL_BP", "혈압 측정", 30),
    ("EXERCISE_30", "운동 30분 이상", 50),
    ("WATER_CHALLENGE", "물 2L 마시기", 20),
    ("DAILY_HEALTH_LOG", "건강 일지 작성", 40),
]

PET_CATALOG = [
    {
        "catalog_id": "PET_DOG",
        "pet_type": PetType.DOG,
        "display_name": "강아지",
        "required_streak_days": 0,
        "affinity_score": 3,
    },
    {
        "catalog_id": "PET_CAT",
        "pet_type": PetType.CAT,
        "display_name": "고양이",
        "required_streak_days": 0,
        "affinity_score": 3,
    },
    {
        "catalog_id": "PET_RABBIT",
        "pet_type": PetType.RABBIT,
        "display_name": "토끼",
        "required_streak_days": 3,
        "affinity_score": 2,
    },
    {
        "catalog_id": "PET_CAPYBARA",
        "pet_type": PetType.CAPYBARA,
        "display_name": "카피바라",
        "required_streak_days": 7,
        "affinity_score": 1,
    },
    {
        "catalog_id": "PET_HAMSTER",
        "pet_type": PetType.HAMSTER,
        "display_name": "햄스터",
        "required_streak_days": 30,
        "affinity_score": 5,
    },
]


class VirtualPetService:
    async def get_my_pet(self, user: User) -> VirtualPetStatusResponse:
        pet = await VirtualPet.get_or_none(user_id=user.id)
        if pet is None:
            return VirtualPetStatusResponse(has_pet=False)

        today = self._today()
        tasks = await self._build_reward_tasks(user.id, pet.pet_type, today)
        pet.health_percent = await self._calculate_health_percent(user.id, today)
        pet.happiness_percent = await self._calculate_happiness_percent(user.id)
        activities = (
            await VirtualPetActivityLog.filter(user_id=user.id, pet_id=pet.id).order_by("-created_at", "-id").limit(10)
        )
        return VirtualPetStatusResponse(
            has_pet=True,
            pet=self._to_pet_response(pet),
            today_tasks=tasks,
            recent_activities=[self._to_activity_response(item) for item in activities],
        )

    async def create_pet(self, user: User, data: VirtualPetCreateRequest) -> VirtualPetCreateResponse:
        existing = await VirtualPet.get_or_none(user_id=user.id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 펫을 선택했습니다.")

        async with in_transaction():
            pet = await VirtualPet.create(
                user_id=user.id,
                pet_type=data.pet_type,
                pet_name=data.pet_name.strip(),
                level=1,
                experience=0,
                next_level_experience=1000,
                growth_stage=PetGrowthStage.STAGE_1,
            )
            await self._create_activity(
                user_id=user.id,
                pet_id=pet.id,
                activity_type=PetActivityType.PET_CREATED,
                description=f"{data.pet_name.strip()} 펫을 선택했습니다.",
                experience_delta=0,
                source_type="SYSTEM",
                source_id=None,
            )

        return VirtualPetCreateResponse(
            pet_id=pet.id,
            pet_type=pet.pet_type,
            pet_name=pet.pet_name,
            level=pet.level,
            experience=pet.experience,
            growth_stage=pet.growth_stage,
        )

    async def update_pet_name(self, user: User, data: VirtualPetNameUpdateRequest) -> VirtualPetNameUpdateResponse:
        pet = await VirtualPet.get_or_none(user_id=user.id)
        if pet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="선택된 펫이 없습니다.")

        pet.pet_name = data.pet_name.strip()
        async with in_transaction():
            await pet.save(update_fields=["pet_name", "last_updated_at"])
            await self._create_activity(
                user_id=user.id,
                pet_id=pet.id,
                activity_type=PetActivityType.NAME_CHANGED,
                description=f"펫 이름을 {pet.pet_name}(으)로 변경했습니다.",
                experience_delta=0,
                source_type="SYSTEM",
                source_id=None,
            )

        return VirtualPetNameUpdateResponse(pet_id=pet.id, pet_name=pet.pet_name)

    async def claim_reward_tasks(self, user: User) -> PetRewardClaimResponse:
        pet = await VirtualPet.get_or_none(user_id=user.id)
        if pet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="선택된 펫이 없습니다.")

        today = self._today()
        source_id = self._date_key(today)
        tasks = await self._build_reward_tasks(user.id, pet.pet_type, today)
        claimed = await VirtualPetActivityLog.filter(
            user_id=user.id,
            pet_id=pet.id,
            activity_type=PetActivityType.TASK_COMPLETED,
            source_id=source_id,
        )
        claimed_types = {item.source_type for item in claimed}
        claimable_tasks = [task for task in tasks if task.is_completed and task.task_type not in claimed_types]
        self._ensure_claimable_tasks(claimable_tasks)

        awarded_experience = sum(task.reward_experience for task in claimable_tasks)
        self._apply_experience(pet, awarded_experience)

        pet.health_percent = await self._calculate_health_percent(user.id, today)
        pet.happiness_percent = await self._calculate_happiness_percent(user.id)
        async with in_transaction():
            await pet.save(
                update_fields=[
                    "level",
                    "experience",
                    "next_level_experience",
                    "growth_stage",
                    "health_percent",
                    "happiness_percent",
                    "last_updated_at",
                ]
            )
            for task in claimable_tasks:
                await self._create_activity(
                    user_id=user.id,
                    pet_id=pet.id,
                    activity_type=PetActivityType.TASK_COMPLETED,
                    description=f"{task.title} 완료",
                    experience_delta=task.reward_experience,
                    source_type=task.task_type,
                    source_id=source_id,
                )

        return PetRewardClaimResponse(
            awarded_experience=awarded_experience,
            claimed_task_count=len(claimable_tasks),
            level=pet.level,
            experience=pet.experience,
            next_level_experience=pet.next_level_experience,
            growth_stage=pet.growth_stage,
        )

    @staticmethod
    def _ensure_claimable_tasks(claimable_tasks: list[PetRewardTaskResponse]) -> None:
        if not claimable_tasks:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="수령 가능한 오늘의 펫 보상이 없습니다.")

    async def get_pet_catalog(self, user: User, pet_type: PetType | None = None) -> PetCatalogResponse:
        current_streak_days = await self._current_challenge_streak_days(user.id, self._today())
        current_pet = await VirtualPet.get_or_none(user_id=user.id)
        current_pet_type = current_pet.pet_type if current_pet else None
        catalog_items = [item for item in PET_CATALOG if pet_type is None or item["pet_type"] == pet_type]
        items = [self._to_catalog_item(item, current_streak_days, current_pet_type) for item in catalog_items]
        unlocked_count = sum(1 for item in items if item.is_unlocked)
        return PetCatalogResponse(
            summary=PetCatalogSummaryResponse(
                total_count=len(items),
                unlocked_count=unlocked_count,
                completion_rate=round(self._percent(unlocked_count, len(items)), 1),
            ),
            items=items,
        )

    @staticmethod
    async def _create_activity(
        user_id: int,
        pet_id: int,
        activity_type: PetActivityType,
        description: str,
        experience_delta: int,
        source_type: str | None,
        source_id: int | None,
    ) -> None:
        await VirtualPetActivityLog.create(
            user_id=user_id,
            pet_id=pet_id,
            activity_type=activity_type,
            description=description,
            experience_delta=experience_delta,
            source_type=source_type,
            source_id=source_id,
        )

    async def _build_reward_tasks(
        self, user_id: int, pet_type: PetType, target_date: date
    ) -> list[PetRewardTaskResponse]:
        completion_map = await self._task_completion_map(user_id, target_date)
        return [
            PetRewardTaskResponse(
                task_type=task_type,
                title=title,
                reward_experience=self._reward_experience(task_type, reward, pet_type),
                is_completed=completion_map[task_type],
            )
            for task_type, title, reward in BASE_REWARD_TASKS
        ]

    async def _task_completion_map(self, user_id: int, target_date: date) -> dict[str, bool]:
        exercise_logs = await ExerciseLog.filter(user_id=user_id, exercise_date=target_date)
        exercise_minutes = sum(record.duration_minutes for record in exercise_logs)
        water_checkin_exists = await ChallengeCheckin.filter(
            user_id=user_id,
            checkin_date=target_date,
            participation__challenge__target_metric="WATER",
        ).exists()
        return {
            "VITAL_BP": await VitalRecord.filter(
                user_id=user_id,
                record_date=target_date,
                measure_type__startswith="BP_",
            ).exists(),
            "EXERCISE_30": exercise_minutes >= 30,
            "WATER_CHALLENGE": water_checkin_exists,
            "DAILY_HEALTH_LOG": await ActivityLog.filter(user_id=user_id, record_date=target_date).exists(),
        }

    async def _calculate_health_percent(self, user_id: int, today: date) -> int:
        total = 0
        completed = 0
        for offset in range(7):
            target_date = today - timedelta(days=offset)
            completion_map = await self._task_completion_map(user_id, target_date)
            total += len(completion_map)
            completed += sum(1 for is_completed in completion_map.values() if is_completed)
        return self._percent(completed, total)

    @staticmethod
    async def _calculate_happiness_percent(user_id: int) -> int:
        participations = await ChallengeParticipation.filter(user_id=user_id).prefetch_related("challenge")
        total_days = sum(participation.challenge.duration_days for participation in participations)
        completed_days = sum(
            min(participation.progress_count, participation.challenge.duration_days) for participation in participations
        )
        return VirtualPetService._percent(completed_days, total_days)

    @staticmethod
    async def _current_challenge_streak_days(user_id: int, today: date) -> int:
        checkins = await ChallengeCheckin.filter(user_id=user_id)
        checkin_dates = {checkin.checkin_date for checkin in checkins}
        streak = 0
        current = today
        while current in checkin_dates:
            streak += 1
            current -= timedelta(days=1)
        return streak

    @staticmethod
    def _to_catalog_item(
        item: dict,
        current_streak_days: int,
        current_pet_type: PetType | None | object = _CURRENT_PET_TYPE_UNSET,
    ) -> PetCatalogItemResponse:
        required_streak_days = item["required_streak_days"]
        is_selected_pet = item["pet_type"] == current_pet_type
        if current_pet_type is _CURRENT_PET_TYPE_UNSET:
            is_unlocked = current_streak_days >= required_streak_days
        elif required_streak_days <= 0:
            is_unlocked = is_selected_pet
        else:
            is_unlocked = is_selected_pet or current_streak_days >= required_streak_days
        return PetCatalogItemResponse(
            catalog_id=item["catalog_id"],
            pet_type=item["pet_type"],
            display_name=item["display_name"] if is_unlocked else "???",
            is_unlocked=is_unlocked,
            unlock_condition=VirtualPetService._unlock_condition(required_streak_days),
            affinity_score=item["affinity_score"] if is_unlocked else None,
        )

    @staticmethod
    def _unlock_condition(required_streak_days: int) -> str:
        if required_streak_days <= 0:
            return "기본 제공"
        return f"챌린지 {required_streak_days}일 연속 달성"

    @staticmethod
    def _reward_experience(task_type: str, base_reward: int, pet_type: PetType) -> int:
        if pet_type == PetType.DOG and task_type == "EXERCISE_30":
            return round(base_reward * 1.2)
        if pet_type == PetType.CAT and task_type == "DAILY_HEALTH_LOG":
            return round(base_reward * 1.2)
        if pet_type == PetType.RABBIT and task_type == "VITAL_BP":
            return round(base_reward * 1.2)
        if pet_type == PetType.CAPYBARA and task_type == "WATER_CHALLENGE":
            return round(base_reward * 1.2)
        if pet_type == PetType.HAMSTER and task_type == "DAILY_HEALTH_LOG":
            return round(base_reward * 1.1)
        return base_reward

    @staticmethod
    def _apply_experience(pet: VirtualPet, amount: int) -> None:
        pet.experience += amount
        while pet.experience >= pet.next_level_experience:
            pet.experience -= pet.next_level_experience
            pet.level += 1
            pet.next_level_experience = pet.level * 1000
        pet.growth_stage = VirtualPetService._growth_stage(pet.level)

    @staticmethod
    def _growth_stage(level: int) -> PetGrowthStage:
        if level >= 10:
            return PetGrowthStage.STAGE_3
        if level >= 5:
            return PetGrowthStage.STAGE_2
        return PetGrowthStage.STAGE_1

    @staticmethod
    def _percent(numerator: int, denominator: int) -> int:
        if denominator <= 0:
            return 0
        return round(min(numerator / denominator, 1) * 100)

    @staticmethod
    def _date_key(target_date: date) -> int:
        return int(target_date.strftime(DATE_KEY_FORMAT))

    @staticmethod
    def _today() -> date:
        return datetime.now(config.TIMEZONE).date()

    @staticmethod
    def _to_pet_response(pet: VirtualPet) -> VirtualPetResponse:
        return VirtualPetResponse(
            pet_id=pet.id,
            pet_type=pet.pet_type,
            pet_name=pet.pet_name,
            level=pet.level,
            experience=pet.experience,
            next_level_experience=pet.next_level_experience,
            growth_stage=pet.growth_stage,
            health_percent=pet.health_percent,
            happiness_percent=pet.happiness_percent,
        )

    @staticmethod
    def _to_activity_response(activity: VirtualPetActivityLog) -> PetRecentActivityResponse:
        return PetRecentActivityResponse(
            activity_type=activity.activity_type,
            description=activity.description,
            experience_delta=activity.experience_delta,
            created_at=activity.created_at,
        )
