from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.dtos.pets import (
    PetRecentActivityResponse,
    VirtualPetCreateRequest,
    VirtualPetCreateResponse,
    VirtualPetNameUpdateRequest,
    VirtualPetNameUpdateResponse,
    VirtualPetResponse,
    VirtualPetStatusResponse,
)
from app.models.pets import PetActivityType, PetGrowthStage, VirtualPet, VirtualPetActivityLog
from app.models.users import User


class VirtualPetService:
    async def get_my_pet(self, user: User) -> VirtualPetStatusResponse:
        pet = await VirtualPet.get_or_none(user_id=user.id)
        if pet is None:
            return VirtualPetStatusResponse(has_pet=False)

        activities = (
            await VirtualPetActivityLog.filter(user_id=user.id, pet_id=pet.id).order_by("-created_at", "-id").limit(10)
        )
        return VirtualPetStatusResponse(
            has_pet=True,
            pet=self._to_pet_response(pet),
            today_tasks=[],
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
            )

        return VirtualPetNameUpdateResponse(pet_id=pet.id, pet_name=pet.pet_name)

    @staticmethod
    async def _create_activity(
        user_id: int,
        pet_id: int,
        activity_type: PetActivityType,
        description: str,
        experience_delta: int,
    ) -> None:
        await VirtualPetActivityLog.create(
            user_id=user_id,
            pet_id=pet_id,
            activity_type=activity_type,
            description=description,
            experience_delta=experience_delta,
            source_type="SYSTEM",
        )

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
