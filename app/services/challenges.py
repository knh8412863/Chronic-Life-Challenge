from datetime import date, timedelta
from types import SimpleNamespace

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.dtos.challenges import (
    ChallengeBadgeItemResponse,
    ChallengeBadgeListResponse,
    ChallengeCancelResponse,
    ChallengeCheckinCreateRequest,
    ChallengeCheckinResponse,
    ChallengeDashboardSummaryResponse,
    ChallengeDetailResponse,
    ChallengeDisplayCategory,
    ChallengeJoinResponse,
    ChallengeLeaderboardItemResponse,
    ChallengeLeaderboardMyRankResponse,
    ChallengeParticipationStatus,
    ChallengeSummaryResponse,
    ChallengeTodayMissionResponse,
    ChallengeWeeklyActivityResponse,
    ChallengeWeeklyLeaderboardResponse,
    MyChallengeResponse,
)
from app.models.challenges import (
    Challenge,
    ChallengeCheckin,
    ChallengeDiseaseTag,
    ChallengeLeaderboard,
    ChallengeParticipation,
    UserBadge,
)
from app.models.predictions import ActivityLog, ExerciseLog, LipidObesityRecord, MealLog, RenalRecord, VitalRecord
from app.models.users import User
from app.services.account_stats import sync_user_account_stats
from app.services.managed_diseases import get_user_managed_disease_codes
from app.services.notifications import NotificationService

DEFAULT_CHALLENGES = [
    {
        "title": "30일 걷기 챌린지",
        "description": "매일 걸음 수 목표를 달성해 건강한 걷기 습관을 만듭니다.",
        "category": "WALK",
        "target_metric": "STEPS",
        "goal_value": 6000,
        "duration_days": 30,
    },
    {
        "title": "수분 섭취 챌린지",
        "description": "매일 충분한 물 섭취를 기록해 수분 관리 습관을 만듭니다.",
        "category": "WATER",
        "target_metric": "WATER",
        "goal_value": 8,
        "duration_days": 14,
    },
    {
        "title": "저염식 습관 챌린지",
        "description": "나트륨 섭취를 줄이는 식단 실천을 기록합니다.",
        "category": "DIET",
        "target_metric": "DIET",
        "goal_value": 1,
        "duration_days": 14,
    },
    {
        "title": "규칙적 운동 챌린지",
        "description": "꾸준한 운동 기록으로 활동량을 높입니다.",
        "category": "EXERCISE",
        "target_metric": "EXERCISE",
        "goal_value": 30,
        "duration_days": 21,
    },
    {
        "title": "종합 건강 관리",
        "description": "걷기, 수분 섭취, 식단, 운동 기록을 균형 있게 실천합니다.",
        "category": "COMPREHENSIVE",
        "target_metric": "DAILY_CHECKIN",
        "goal_value": 1,
        "duration_days": 28,
    },
]
DEFAULT_CHALLENGE_DISEASE_TAGS = {
    "30일 걷기 챌린지": {
        "DIABETES": 10,
        "HYPERTENSION": 20,
        "OBESITY": 30,
        "DYSLIPIDEMIA": 40,
    },
    "수분 섭취 챌린지": {
        "CKD": 10,
        "DIABETES": 30,
    },
    "저염식 습관 챌린지": {
        "HYPERTENSION": 10,
        "CKD": 20,
    },
    "규칙적 운동 챌린지": {
        "DIABETES": 10,
        "HYPERTENSION": 20,
        "OBESITY": 30,
        "DYSLIPIDEMIA": 40,
    },
    "종합 건강 관리": {
        "DIABETES": 10,
        "HYPERTENSION": 20,
        "CKD": 30,
        "OBESITY": 40,
        "DYSLIPIDEMIA": 50,
    },
}

BADGE_DEFINITIONS = [
    {
        "badge_type": "STREAK_3",
        "badge_name": "3일 연속 성공",
        "target_streak": 3,
        "bonus_points": 3,
    },
    {
        "badge_type": "STREAK_7",
        "badge_name": "7일 연속 성공",
        "target_streak": 7,
        "bonus_points": 5,
    },
    {
        "badge_type": "STREAK_30",
        "badge_name": "30일 연속 성공",
        "target_streak": 30,
        "bonus_points": 10,
    },
]


class ChallengeService:
    async def get_challenges(
        self,
        user: User,
        category: str | None = None,
        target_metric: str | None = None,
        sort: str = "LATEST",
    ) -> list[ChallengeSummaryResponse]:
        await self._ensure_default_challenges()
        today = date.today()
        await self._sync_today_checkins_from_health_records(user, today)
        query = Challenge.filter(is_active=True)
        if category:
            query = query.filter(category=category)
        if target_metric:
            query = query.filter(target_metric=target_metric)

        challenges = await query.order_by("id")
        challenge_ids = [challenge.id for challenge in challenges]
        active_participations = (
            await ChallengeParticipation.filter(
                user_id=user.id,
                status=ChallengeParticipationStatus.JOINED.value,
            )
            .prefetch_related("checkins")
            .all()
        )
        participation_counts = await self._participant_counts(challenge_ids)
        joined_ids = {participation.challenge_id for participation in active_participations}
        today_checked_ids = {
            participation.challenge_id
            for participation in active_participations
            if any(checkin.checkin_date == today for checkin in participation.checkins)
        }
        today_context = await self._today_health_context(user.id, today)
        summaries = [
            self._to_summary(
                challenge,
                is_joined=challenge.id in joined_ids,
                today_checked=challenge.id in today_checked_ids
                or self._health_context_satisfies_challenge(challenge, today_context),
                participant_count=participation_counts.get(challenge.id, 0),
            )
            for challenge in challenges
        ]
        return self._sort_challenge_summaries(summaries, sort)

    async def get_challenge(self, user: User, challenge_id: int) -> ChallengeDetailResponse:
        await self._ensure_default_challenges()
        today = date.today()
        await self._sync_today_checkins_from_health_records(user, today)
        challenge = await self._get_active_challenge(challenge_id)
        participation = await ChallengeParticipation.get_or_none(
            user_id=user.id,
            challenge_id=challenge.id,
            status=ChallengeParticipationStatus.JOINED.value,
        ).prefetch_related("checkins")
        participations = (
            await ChallengeParticipation.filter(challenge_id=challenge.id)
            .prefetch_related("challenge", "checkins")
            .all()
        )
        participant_count = len(participations)
        today_context = await self._today_health_context(user.id, today)
        today_checked = bool(
            participation
            and (
                any(checkin.checkin_date == today for checkin in participation.checkins)
                or self._health_context_satisfies_challenge(challenge, today_context)
            )
        )
        return ChallengeDetailResponse(
            **self._to_summary(
                challenge,
                is_joined=participation is not None,
                today_checked=today_checked,
                participant_count=participant_count,
            ).model_dump(),
            average_completion_rate=self._average_completion_rate(participations),
            how_to_join=self._how_to_join_steps(challenge),
            daily_mission_examples=self._daily_mission_examples(challenge),
            created_at=challenge.created_at,
            updated_at=challenge.updated_at,
        )

    async def join_challenge(self, user: User, challenge_id: int) -> ChallengeJoinResponse:
        await self._ensure_default_challenges()
        challenge = await self._get_active_challenge(challenge_id)
        existing = await ChallengeParticipation.get_or_none(
            user_id=user.id,
            challenge_id=challenge.id,
            status=ChallengeParticipationStatus.JOINED.value,
        ).prefetch_related("challenge")
        if existing:
            return self._to_join_response(existing)

        today = date.today()
        participation = await ChallengeParticipation.create(
            user=user,
            challenge=challenge,
            start_date=today,
            end_date=today + timedelta(days=challenge.duration_days - 1),
            status=ChallengeParticipationStatus.JOINED.value,
        )
        return self._to_join_response(participation)

    async def get_my_challenges(self, user: User) -> list[MyChallengeResponse]:
        await self._ensure_default_challenges()
        today = date.today()
        await self._sync_today_checkins_from_health_records(user, today)
        participations = (
            await ChallengeParticipation.filter(user_id=user.id)
            .order_by("-created_at")
            .prefetch_related("challenge", "checkins")
        )
        today_context = await self._today_health_context(user.id, today)
        return [self._to_my_challenge(participation, today, today_context) for participation in participations]

    async def get_participation(self, user: User, participation_id: int) -> MyChallengeResponse:
        participation = await ChallengeParticipation.get_or_none(id=participation_id, user_id=user.id).prefetch_related(
            "challenge",
            "checkins",
        )
        if participation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="참여 중인 챌린지를 찾을 수 없습니다.")
        today = date.today()
        today_context = await self._today_health_context(user.id, today)
        return self._to_my_challenge(participation, today, today_context)

    async def get_recommendations(self, user: User, limit: int = 5) -> list[ChallengeSummaryResponse]:
        await self._ensure_default_challenges()
        managed_diseases = await get_user_managed_disease_codes(user.id)
        challenges = await self.get_challenges(user, sort="POPULAR")
        available = [challenge for challenge in challenges if not challenge.is_joined]
        if not managed_diseases:
            return available[:limit]

        tagged_rows = await ChallengeDiseaseTag.filter(disease_code__in=managed_diseases).values(
            "challenge_id",
            "disease_code",
            "priority",
        )
        ranked_ids = self._rank_challenge_ids_by_disease_tags(tagged_rows, managed_diseases)
        return self._rank_recommendations_by_tags(available, ranked_ids)[:limit]

    async def get_dashboard_summary(self, user: User) -> ChallengeDashboardSummaryResponse:
        today = date.today()
        await self._sync_today_checkins_from_health_records(user, today)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        participations = (
            await ChallengeParticipation.filter(user_id=user.id)
            .order_by("-created_at")
            .prefetch_related("challenge", "checkins")
        )
        earned_badge_count = await UserBadge.filter(user_id=user.id).count()

        today_context = await self._today_health_context(user.id, today)
        return self._build_dashboard_summary(
            participations, today, week_start, week_end, earned_badge_count, today_context
        )

    async def get_badges(self, user: User, badge_filter: str = "ALL") -> ChallengeBadgeListResponse:
        checkins = await ChallengeCheckin.filter(user_id=user.id).order_by("-checkin_date", "-created_at")
        badges = await UserBadge.filter(user_id=user.id).order_by("-earned_at").all()
        return self._build_badge_list(checkins, date.today(), badge_filter, badges)

    async def get_weekly_leaderboard(
        self,
        user: User,
        week_start: date | None = None,
        limit: int = 10,
    ) -> ChallengeWeeklyLeaderboardResponse:
        target_week_start = week_start or self._current_week_start(date.today())
        week_end = target_week_start + timedelta(days=6)
        challenge_ids = await ChallengeParticipation.filter(
            user_id=user.id,
            status=ChallengeParticipationStatus.JOINED.value,
        ).values_list("challenge_id", flat=True)
        if not challenge_ids:
            return self._build_weekly_leaderboard(
                entries=[],
                my_entry=None,
                current_user_id=user.id,
                week_start=target_week_start,
                week_end=week_end,
            )

        all_entries = await self._build_shared_challenge_leaderboard_entries(
            current_user_id=user.id,
            challenge_ids=list(challenge_ids),
            week_start=target_week_start,
            week_end=week_end,
        )
        entries = all_entries[:limit]
        my_entry = next((entry for entry in all_entries if entry.user_id == user.id), None)
        return self._build_weekly_leaderboard(
            entries=entries,
            my_entry=my_entry,
            current_user_id=user.id,
            week_start=target_week_start,
            week_end=week_end,
        )

    @staticmethod
    async def _build_shared_challenge_leaderboard_entries(
        current_user_id: int,
        challenge_ids: list[int],
        week_start: date,
        week_end: date,
    ) -> list[SimpleNamespace]:
        user_ids = (
            await ChallengeParticipation.filter(
                challenge_id__in=challenge_ids,
                status__in=[
                    ChallengeParticipationStatus.JOINED.value,
                    ChallengeParticipationStatus.COMPLETED.value,
                ],
            )
            .distinct()
            .values_list("user_id", flat=True)
        )
        users = await User.filter(id__in=list(user_ids))
        entries = []
        for participant in users:
            completed_count = await ChallengeCheckin.filter(
                user_id=participant.id,
                participation__challenge_id__in=challenge_ids,
                checkin_date__gte=week_start,
                checkin_date__lte=week_end,
            ).count()
            if participant.id != current_user_id and completed_count == 0:
                continue
            entries.append(
                SimpleNamespace(
                    user_id=participant.id,
                    nickname_masked=ChallengeService._mask_name(participant.name),
                    total_points=completed_count * 10,
                    completed_mission_count=completed_count,
                    rank_no=0,
                )
            )

        entries.sort(key=lambda item: (-item.total_points, -item.completed_mission_count, item.user_id))
        for rank, entry in enumerate(entries, start=1):
            entry.rank_no = rank
        return entries

    async def checkin_today(
        self,
        user: User,
        participation_id: int,
        data: ChallengeCheckinCreateRequest,
    ) -> ChallengeCheckinResponse:
        participation = await ChallengeParticipation.get_or_none(
            id=participation_id,
            user_id=user.id,
        ).prefetch_related("challenge")
        if participation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="참여 중인 챌린지를 찾을 수 없습니다.")
        if participation.status != ChallengeParticipationStatus.JOINED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="진행 중인 챌린지만 체크인할 수 있습니다.")

        today = date.today()
        if today < participation.start_date or today > participation.end_date:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="챌린지 진행 기간이 아닙니다.")

        async with in_transaction():
            exists = await ChallengeCheckin.exists(participation_id=participation.id, checkin_date=today)
            if exists:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="오늘은 이미 체크인했습니다.")

            checkin = await ChallengeCheckin.create(
                participation=participation,
                user=user,
                checkin_date=today,
                note=data.note,
            )
            participation.progress_count += 1
            if participation.progress_count >= participation.challenge.duration_days:
                participation.status = ChallengeParticipationStatus.COMPLETED.value
                participation.completed_at = checkin.created_at
            await participation.save(update_fields=["progress_count", "status", "completed_at", "updated_at"])
            current_streak = await self._current_user_streak(user.id, today)
            await self._award_streak_badges(user=user, challenge=participation.challenge, current_streak=current_streak)
            await self._upsert_weekly_leaderboard(user=user, week_start=self._current_week_start(today))

        await NotificationService().notify_challenge_checkin(
            user_id=user.id,
            challenge_title=participation.challenge.title,
            completed=participation.status == ChallengeParticipationStatus.COMPLETED.value,
        )
        return self._to_checkin_response(checkin, participation)

    async def _sync_today_checkins_from_health_records(self, user: User, today: date) -> None:
        participations = (
            await ChallengeParticipation.filter(
                user_id=user.id,
                status=ChallengeParticipationStatus.JOINED.value,
                start_date__lte=today,
                end_date__gte=today,
            )
            .prefetch_related("challenge")
            .all()
        )
        if not participations:
            return

        context = await self._today_health_context(user.id, today)
        synced = False
        for participation in participations:
            if not self._health_context_satisfies_challenge(participation.challenge, context):
                continue

            async with in_transaction():
                exists = await ChallengeCheckin.exists(participation_id=participation.id, checkin_date=today)
                if exists:
                    continue

                checkin = await ChallengeCheckin.create(
                    participation=participation,
                    user=user,
                    checkin_date=today,
                    note="건강 기록 입력으로 자동 완료",
                )
                participation.progress_count += 1
                if participation.progress_count >= participation.challenge.duration_days:
                    participation.status = ChallengeParticipationStatus.COMPLETED.value
                    participation.completed_at = checkin.created_at
                await participation.save(update_fields=["progress_count", "status", "completed_at", "updated_at"])
                current_streak = await self._current_user_streak(user.id, today)
                await self._award_streak_badges(
                    user=user,
                    challenge=participation.challenge,
                    current_streak=current_streak,
                )
                synced = True

        if synced:
            await self._upsert_weekly_leaderboard(user=user, week_start=self._current_week_start(today))

    @staticmethod
    async def _today_health_context(user_id: int, today: date) -> dict[str, object]:
        activities = await ActivityLog.filter(user_id=user_id, record_date=today)
        exercises = await ExerciseLog.filter(user_id=user_id, exercise_date=today)
        meal_count = await MealLog.filter(user_id=user_id, meal_date=today).count()
        vital_count = await VitalRecord.filter(user_id=user_id, record_date=today).count()
        lipid_count = await LipidObesityRecord.filter(user_id=user_id, record_date=today).count()
        renal_count = await RenalRecord.filter(user_id=user_id, record_date=today).count()

        activity_exercise_minutes = sum(item.exercise_minutes or 0 for item in activities)
        exercise_log_minutes = sum(item.duration_minutes or 0 for item in exercises)
        walking_minutes = sum(
            item.duration_minutes or 0 for item in exercises if str(item.exercise_type).upper() == "WALKING"
        )

        return {
            "steps": max([item.steps or 0 for item in activities], default=0),
            "water_ml": max([item.water_ml or 0 for item in activities], default=0),
            "exercise_minutes": max(activity_exercise_minutes, exercise_log_minutes),
            "walking_minutes": walking_minutes,
            "sleep_hours": max([float(item.sleep_hours or 0) for item in activities], default=0.0),
            "meal_count": meal_count,
            "health_record_count": meal_count
            + vital_count
            + lipid_count
            + renal_count
            + len(activities)
            + len(exercises),
        }

    @staticmethod
    def _health_context_satisfies_challenge(challenge: Challenge, context: dict[str, object]) -> bool:
        metric = str(challenge.target_metric).upper()
        goal_value = int(challenge.goal_value or 1)

        if metric == "STEPS":
            return int(context.get("steps") or 0) >= goal_value or int(context.get("walking_minutes") or 0) >= 30
        if metric == "WATER":
            water_goal_ml = goal_value * 250 if goal_value <= 20 else goal_value
            return int(context.get("water_ml") or 0) >= water_goal_ml
        if metric == "EXERCISE":
            return int(context.get("exercise_minutes") or 0) >= goal_value
        if metric == "SLEEP":
            return float(context.get("sleep_hours") or 0) >= goal_value
        if metric == "DIET":
            return int(context.get("meal_count") or 0) >= goal_value
        if metric == "DAILY_CHECKIN":
            return int(context.get("health_record_count") or 0) >= goal_value

        return False

    async def cancel_participation(self, user: User, participation_id: int) -> ChallengeCancelResponse:
        participation = await ChallengeParticipation.get_or_none(
            id=participation_id,
            user_id=user.id,
        ).prefetch_related("challenge")
        if participation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="참여 중인 챌린지를 찾을 수 없습니다.")
        if participation.status != ChallengeParticipationStatus.JOINED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="진행 중인 챌린지만 포기할 수 있습니다.")

        participation.status = ChallengeParticipationStatus.CANCELED.value
        await participation.save(update_fields=["status", "updated_at"])
        return self._to_cancel_response(participation)

    @staticmethod
    async def _ensure_default_challenges() -> None:
        default_titles = [challenge["title"] for challenge in DEFAULT_CHALLENGES]
        existing_titles = set(await Challenge.filter(title__in=default_titles).values_list("title", flat=True))
        missing_challenges = [
            Challenge(**challenge) for challenge in DEFAULT_CHALLENGES if challenge["title"] not in existing_titles
        ]
        if missing_challenges:
            await Challenge.bulk_create(missing_challenges)
        await ChallengeService._ensure_default_challenge_disease_tags()

    @staticmethod
    async def _ensure_default_challenge_disease_tags() -> None:
        challenges = await Challenge.filter(title__in=list(DEFAULT_CHALLENGE_DISEASE_TAGS)).all()
        challenge_by_title = {challenge.title: challenge for challenge in challenges}
        for title, tags in DEFAULT_CHALLENGE_DISEASE_TAGS.items():
            challenge = challenge_by_title.get(title)
            if challenge is None:
                continue
            for disease_code, priority in tags.items():
                await ChallengeDiseaseTag.get_or_create(
                    challenge_id=challenge.id,
                    disease_code=disease_code,
                    defaults={"priority": priority},
                )

    @staticmethod
    async def _get_active_challenge(challenge_id: int) -> Challenge:
        challenge = await Challenge.get_or_none(id=challenge_id, is_active=True)
        if challenge is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="챌린지를 찾을 수 없습니다.")
        return challenge

    @staticmethod
    def _to_summary(
        challenge: Challenge,
        is_joined: bool,
        today_checked: bool = False,
        participant_count: int = 0,
    ) -> ChallengeSummaryResponse:
        return ChallengeSummaryResponse(
            challenge_id=challenge.id,
            title=challenge.title,
            description=challenge.description,
            category=ChallengeService._display_category(challenge),
            target_metric=challenge.target_metric,
            goal_value=challenge.goal_value,
            duration_days=challenge.duration_days,
            difficulty=ChallengeService._difficulty(challenge.duration_days),
            reward_points=ChallengeService._reward_points(challenge.duration_days),
            participant_count=participant_count,
            is_joined=is_joined,
            today_checked=today_checked,
        )

    @staticmethod
    def _display_category(challenge: Challenge) -> ChallengeDisplayCategory:
        category = str(challenge.category).upper()
        target_metric = str(challenge.target_metric).upper()
        if category in ChallengeDisplayCategory.__members__:
            return ChallengeDisplayCategory(category)
        if category in {"HYDRATION", "WATER"} or target_metric == "WATER":
            return ChallengeDisplayCategory.WATER
        if category in {"WALK", "STEPS"} or target_metric == "STEPS":
            return ChallengeDisplayCategory.WALK
        if category == "EXERCISE" or target_metric == "EXERCISE":
            return ChallengeDisplayCategory.EXERCISE
        if category == "SLEEP" or target_metric == "SLEEP":
            return ChallengeDisplayCategory.SLEEP
        if category == "DIET" or target_metric == "DIET":
            return ChallengeDisplayCategory.DIET
        return ChallengeDisplayCategory.COMPREHENSIVE

    @staticmethod
    def _to_join_response(participation: ChallengeParticipation) -> ChallengeJoinResponse:
        return ChallengeJoinResponse(
            participation_id=participation.id,
            challenge_id=participation.challenge_id,
            status=ChallengeParticipationStatus(participation.status),
            start_date=participation.start_date,
            end_date=participation.end_date,
            progress_count=participation.progress_count,
            completion_rate=ChallengeService._completion_rate(
                participation.progress_count,
                participation.challenge.duration_days,
            ),
            created_at=participation.created_at,
        )

    @staticmethod
    def _to_my_challenge(
        participation: ChallengeParticipation,
        today: date,
        today_context: dict[str, object] | None = None,
    ) -> MyChallengeResponse:
        today_checked = any(checkin.checkin_date == today for checkin in participation.checkins)
        if not today_checked and today_context is not None:
            today_checked = ChallengeService._health_context_satisfies_challenge(participation.challenge, today_context)
        return MyChallengeResponse(
            participation_id=participation.id,
            challenge_id=participation.challenge.id,
            title=participation.challenge.title,
            status=ChallengeParticipationStatus(participation.status),
            start_date=participation.start_date,
            end_date=participation.end_date,
            progress_count=participation.progress_count,
            duration_days=participation.challenge.duration_days,
            completion_rate=ChallengeService._completion_rate(
                participation.progress_count,
                participation.challenge.duration_days,
            ),
            today_checked=today_checked,
        )

    @staticmethod
    def _build_dashboard_summary(
        participations: list[ChallengeParticipation],
        today: date,
        week_start: date,
        week_end: date,
        earned_badge_count: int = 0,
        today_context: dict[str, object] | None = None,
    ) -> ChallengeDashboardSummaryResponse:
        active_participations = [
            item for item in participations if item.status == ChallengeParticipationStatus.JOINED.value
        ]
        completed_count = sum(
            1 for item in participations if item.status == ChallengeParticipationStatus.COMPLETED.value
        )
        weekly_activity = ChallengeService._build_weekly_activity(participations, week_start)
        completed_mission_count = sum(item.completed_count for item in weekly_activity)
        weekly_completion_rate = ChallengeService._weekly_completion_rate(
            completed_mission_count,
            len(active_participations),
            today,
            week_start,
            week_end,
        )
        checkin_dates = {checkin.checkin_date for participation in participations for checkin in participation.checkins}

        return ChallengeDashboardSummaryResponse(
            active_count=len(active_participations),
            completed_count=completed_count,
            weekly_completion_rate=weekly_completion_rate,
            current_streak_days=ChallengeService._current_streak_days(checkin_dates, today),
            completed_mission_count=completed_mission_count,
            earned_badge_count=earned_badge_count,
            today_missions=ChallengeService._build_today_missions(active_participations, today, today_context),
            weekly_activity=weekly_activity,
        )

    @staticmethod
    def _build_today_missions(
        participations: list[ChallengeParticipation],
        today: date,
        today_context: dict[str, object] | None = None,
    ) -> list[ChallengeTodayMissionResponse]:
        missions = []
        for participation in participations:
            today_checked = any(checkin.checkin_date == today for checkin in participation.checkins)
            if not today_checked and today_context is not None:
                today_checked = ChallengeService._health_context_satisfies_challenge(
                    participation.challenge,
                    today_context,
                )
            missions.append(
                ChallengeTodayMissionResponse(
                    participation_id=participation.id,
                    challenge_id=participation.challenge.id,
                    title=participation.challenge.title,
                    mission_text=ChallengeService._mission_text(participation.challenge),
                    today_checked=today_checked,
                )
            )
        return missions

    @staticmethod
    def _build_weekly_activity(
        participations: list[ChallengeParticipation],
        week_start: date,
    ) -> list[ChallengeWeeklyActivityResponse]:
        counts = {week_start + timedelta(days=offset): 0 for offset in range(7)}
        for participation in participations:
            for checkin in participation.checkins:
                if checkin.checkin_date in counts:
                    counts[checkin.checkin_date] += 1

        return [
            ChallengeWeeklyActivityResponse(activity_date=activity_date, completed_count=completed_count)
            for activity_date, completed_count in counts.items()
        ]

    @staticmethod
    def _weekly_completion_rate(
        completed_mission_count: int,
        active_count: int,
        today: date,
        week_start: date,
        week_end: date,
    ) -> float:
        if active_count <= 0:
            return 0.0
        elapsed_days = (min(today, week_end) - week_start).days + 1
        possible_count = max(elapsed_days * active_count, 1)
        return round(min(completed_mission_count / possible_count, 1.0) * 100, 1)

    @staticmethod
    def _current_streak_days(checkin_dates: set[date], today: date) -> int:
        streak = 0
        current = today
        while current in checkin_dates:
            streak += 1
            current -= timedelta(days=1)
        return streak

    @staticmethod
    def _mission_text(challenge: Challenge) -> str:
        metric_labels = {
            "STEPS": "걸음 수",
            "WATER": "물 섭취",
            "EXERCISE": "운동",
            "SLEEP": "수면",
            "DIET": "식단",
            "DAILY_CHECKIN": "건강 기록",
        }
        metric = metric_labels.get(challenge.target_metric, challenge.target_metric)
        return f"{metric} {challenge.goal_value} 달성하기"

    @staticmethod
    async def _participant_counts(challenge_ids: list[int]) -> dict[int, int]:
        if not challenge_ids:
            return {}
        participations = await ChallengeParticipation.filter(challenge_id__in=challenge_ids).values("challenge_id")
        counts = {challenge_id: 0 for challenge_id in challenge_ids}
        for participation in participations:
            counts[participation["challenge_id"]] += 1
        return counts

    @staticmethod
    def _sort_challenge_summaries(
        summaries: list[ChallengeSummaryResponse],
        sort: str,
    ) -> list[ChallengeSummaryResponse]:
        sort_key = sort.upper()
        if sort_key == "POPULAR":
            return sorted(summaries, key=lambda item: (-item.participant_count, item.challenge_id))
        if sort_key == "DURATION":
            return sorted(summaries, key=lambda item: (item.duration_days, item.challenge_id))
        return sorted(summaries, key=lambda item: item.challenge_id)

    @staticmethod
    def _rank_challenge_ids_by_disease_tags(
        tagged_rows: list[dict],
        managed_diseases: list[str],
    ) -> dict[int, tuple[int, int]]:
        disease_order = {disease_code: index for index, disease_code in enumerate(managed_diseases)}
        ranks: dict[int, tuple[int, int]] = {}
        for row in tagged_rows:
            challenge_id = row["challenge_id"]
            rank = (disease_order.get(row["disease_code"], 999), row["priority"])
            if challenge_id not in ranks or rank < ranks[challenge_id]:
                ranks[challenge_id] = rank
        return ranks

    @staticmethod
    def _rank_recommendations_by_tags(
        challenges: list[ChallengeSummaryResponse],
        ranked_ids: dict[int, tuple[int, int]],
    ) -> list[ChallengeSummaryResponse]:
        tagged = [challenge for challenge in challenges if challenge.challenge_id in ranked_ids]
        fallback = [challenge for challenge in challenges if challenge.challenge_id not in ranked_ids]
        return (
            sorted(
                tagged,
                key=lambda item: (
                    ranked_ids[item.challenge_id][0],
                    ranked_ids[item.challenge_id][1],
                    -item.participant_count,
                    item.challenge_id,
                ),
            )
            + fallback
        )

    @staticmethod
    def _average_completion_rate(participations: list[ChallengeParticipation]) -> float:
        if not participations:
            return 0.0
        rates = [
            ChallengeService._completion_rate(participation.progress_count, participation.challenge.duration_days)
            for participation in participations
        ]
        return round(sum(rates) / len(rates), 1)

    @staticmethod
    def _difficulty(duration_days: int) -> str:
        if duration_days <= 7:
            return "EASY"
        if duration_days <= 14:
            return "NORMAL"
        return "HARD"

    @staticmethod
    def _reward_points(duration_days: int) -> int:
        if duration_days <= 7:
            return 5
        if duration_days <= 14:
            return 10
        return 15

    @staticmethod
    def _how_to_join_steps(challenge: Challenge) -> list[str]:
        return [
            "챌린지 참여 버튼을 눌러 시작합니다.",
            f"{challenge.duration_days}일 동안 매일 미션을 완료합니다.",
            "오늘의 미션을 완료하면 체크인으로 기록합니다.",
        ]

    @staticmethod
    def _daily_mission_examples(challenge: Challenge) -> list[str]:
        return [
            ChallengeService._mission_text(challenge),
            "완료 후 오늘 미션 체크인을 진행합니다.",
        ]

    @staticmethod
    def _to_checkin_response(
        checkin: ChallengeCheckin,
        participation: ChallengeParticipation,
    ) -> ChallengeCheckinResponse:
        return ChallengeCheckinResponse(
            checkin_id=checkin.id,
            participation_id=participation.id,
            checkin_date=checkin.checkin_date,
            progress_count=participation.progress_count,
            status=ChallengeParticipationStatus(participation.status),
            completion_rate=ChallengeService._completion_rate(
                participation.progress_count,
                participation.challenge.duration_days,
            ),
            created_at=checkin.created_at,
        )

    @staticmethod
    def _to_cancel_response(participation: ChallengeParticipation) -> ChallengeCancelResponse:
        return ChallengeCancelResponse(
            participation_id=participation.id,
            challenge_id=participation.challenge_id,
            status=ChallengeParticipationStatus(participation.status),
            canceled_at=participation.updated_at,
        )

    @staticmethod
    def _build_badge_list(
        checkins: list[ChallengeCheckin],
        today: date,
        badge_filter: str,
        earned_badges: list[UserBadge] | None = None,
    ) -> ChallengeBadgeListResponse:
        checkin_dates = {checkin.checkin_date for checkin in checkins}
        current_streak = ChallengeService._current_streak_days(checkin_dates, today)
        earned_by_type = {badge.badge_type: badge for badge in earned_badges or []}

        items = [
            ChallengeService._build_badge_item(
                definition=definition,
                current_streak=current_streak,
                earned_badge=earned_by_type.get(definition["badge_type"]),
            )
            for definition in BADGE_DEFINITIONS
        ]

        filtered_items = ChallengeService._filter_badges(items, badge_filter)
        earned_items = [item for item in items if item.is_earned]
        return ChallengeBadgeListResponse(
            earned_count=len(earned_items),
            total_completion_rate=round(len(earned_items) / len(items) * 100, 1),
            items=filtered_items,
            recent_earned=earned_items[:3],
        )

    @staticmethod
    def _build_badge_item(
        definition: dict,
        current_streak: int,
        earned_badge: UserBadge | None,
    ) -> ChallengeBadgeItemResponse:
        target_streak = definition["target_streak"]
        return ChallengeBadgeItemResponse(
            badge_id=definition["badge_type"].lower(),
            badge_name=definition["badge_name"],
            badge_type=definition["badge_type"],
            is_earned=earned_badge is not None,
            current_streak=current_streak,
            target_streak=target_streak,
            progress_rate=round(min(current_streak / target_streak, 1.0) * 100, 1),
            earned_at=earned_badge.earned_at if earned_badge else None,
        )

    @staticmethod
    def _filter_badges(
        badges: list[ChallengeBadgeItemResponse],
        badge_filter: str,
    ) -> list[ChallengeBadgeItemResponse]:
        if badge_filter == "ALL":
            return badges
        return [badge for badge in badges if badge.badge_type == badge_filter]

    @staticmethod
    def _build_weekly_leaderboard(
        entries: list[ChallengeLeaderboard | SimpleNamespace],
        my_entry: ChallengeLeaderboard | SimpleNamespace | None,
        current_user_id: int,
        week_start: date,
        week_end: date,
    ) -> ChallengeWeeklyLeaderboardResponse:
        items = [ChallengeService._build_leaderboard_item(entry) for entry in entries]
        my_item = next((item for item in items if item.user_id == current_user_id), None)
        if my_item is None and my_entry is not None:
            my_item = ChallengeService._build_leaderboard_item(my_entry)

        return ChallengeWeeklyLeaderboardResponse(
            week_start=week_start,
            week_end=week_end,
            top_three=items[:3],
            my_rank=ChallengeLeaderboardMyRankResponse(
                rank=my_item.rank if my_item else None,
                score=my_item.score if my_item else 0,
                completed_mission_count=my_item.completed_mission_count if my_item else 0,
            ),
            items=items,
        )

    @staticmethod
    def _build_leaderboard_item(entry: ChallengeLeaderboard | SimpleNamespace) -> ChallengeLeaderboardItemResponse:
        return ChallengeLeaderboardItemResponse(
            rank=entry.rank_no or 0,
            user_id=entry.user_id,
            nickname_masked=entry.nickname_masked,
            score=entry.total_points,
            completed_mission_count=entry.completed_mission_count,
        )

    @staticmethod
    def _mask_name(name: str) -> str:
        if not name:
            return "익명"
        if len(name) == 1:
            return "*"
        if len(name) == 2:
            return f"{name[0]}*"
        return f"{name[0]}{'*' * (len(name) - 2)}{name[-1]}"

    @staticmethod
    def _current_week_start(today: date) -> date:
        return today - timedelta(days=today.weekday())

    @staticmethod
    async def _current_user_streak(user_id: int, today: date) -> int:
        checkins = await ChallengeCheckin.filter(user_id=user_id, checkin_date__lte=today).values("checkin_date")
        return ChallengeService._current_streak_days({row["checkin_date"] for row in checkins}, today)

    @staticmethod
    async def _award_streak_badges(user: User, challenge: Challenge, current_streak: int) -> None:
        awarded = False
        for definition in BADGE_DEFINITIONS:
            if current_streak < definition["target_streak"]:
                continue
            _, created = await UserBadge.get_or_create(
                user_id=user.id,
                challenge_id=challenge.id,
                badge_type=definition["badge_type"],
                defaults={
                    "badge_name": definition["badge_name"],
                    "badge_description": f"{definition['target_streak']}일 연속 챌린지 미션 달성",
                    "target_streak": definition["target_streak"],
                    "bonus_points": definition["bonus_points"],
                },
            )
            awarded = awarded or created
        if awarded:
            await sync_user_account_stats(user.id)

    @staticmethod
    async def _upsert_weekly_leaderboard(user: User, week_start: date) -> None:
        week_end = week_start + timedelta(days=6)
        completed_mission_count = await ChallengeCheckin.filter(
            user_id=user.id,
            checkin_date__gte=week_start,
            checkin_date__lte=week_end,
        ).count()
        await ChallengeLeaderboard.update_or_create(
            defaults={
                "nickname_masked": ChallengeService._mask_name(user.name),
                "total_points": completed_mission_count * 10,
                "completed_mission_count": completed_mission_count,
            },
            user_id=user.id,
            week_start_date=week_start,
        )
        await ChallengeService._rebuild_weekly_leaderboard(week_start)

    @staticmethod
    async def _rebuild_weekly_leaderboard(week_start: date) -> None:
        entries = await ChallengeLeaderboard.filter(week_start_date=week_start).order_by(
            "-total_points", "-completed_mission_count", "user_id"
        )
        for rank, entry in enumerate(entries, start=1):
            if entry.rank_no != rank:
                entry.rank_no = rank
                await entry.save(update_fields=["rank_no", "updated_at"])

    @staticmethod
    def _completion_rate(progress_count: int, duration_days: int) -> float:
        if duration_days <= 0:
            return 0.0
        return round(min(progress_count / duration_days, 1.0) * 100, 1)
