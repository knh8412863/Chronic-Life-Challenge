from datetime import date, timedelta

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.dtos.challenges import (
    ChallengeCancelResponse,
    ChallengeCheckinCreateRequest,
    ChallengeCheckinResponse,
    ChallengeDashboardSummaryResponse,
    ChallengeDetailResponse,
    ChallengeJoinResponse,
    ChallengeParticipationStatus,
    ChallengeSummaryResponse,
    ChallengeTodayMissionResponse,
    ChallengeWeeklyActivityResponse,
    MyChallengeResponse,
)
from app.models.challenges import Challenge, ChallengeCheckin, ChallengeParticipation
from app.models.users import User


class ChallengeService:
    async def get_challenges(
        self,
        user: User,
        category: str | None = None,
        target_metric: str | None = None,
        sort: str = "LATEST",
    ) -> list[ChallengeSummaryResponse]:
        query = Challenge.filter(is_active=True)
        if category:
            query = query.filter(category=category)
        if target_metric:
            query = query.filter(target_metric=target_metric)

        challenges = await query.order_by("id")
        challenge_ids = [challenge.id for challenge in challenges]
        today = date.today()
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
        summaries = [
            self._to_summary(
                challenge,
                is_joined=challenge.id in joined_ids,
                today_checked=challenge.id in today_checked_ids,
                participant_count=participation_counts.get(challenge.id, 0),
            )
            for challenge in challenges
        ]
        return self._sort_challenge_summaries(summaries, sort)

    async def get_challenge(self, user: User, challenge_id: int) -> ChallengeDetailResponse:
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
        today = date.today()
        participant_count = len(participations)
        today_checked = bool(participation and any(checkin.checkin_date == today for checkin in participation.checkins))
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
        participations = (
            await ChallengeParticipation.filter(user_id=user.id)
            .order_by("-created_at")
            .prefetch_related("challenge", "checkins")
        )
        today = date.today()
        return [self._to_my_challenge(participation, today) for participation in participations]

    async def get_dashboard_summary(self, user: User) -> ChallengeDashboardSummaryResponse:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        participations = (
            await ChallengeParticipation.filter(user_id=user.id)
            .order_by("-created_at")
            .prefetch_related("challenge", "checkins")
        )

        return self._build_dashboard_summary(participations, today, week_start, week_end)

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

        return self._to_checkin_response(checkin, participation)

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
            category=challenge.category,
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
    def _to_my_challenge(participation: ChallengeParticipation, today: date) -> MyChallengeResponse:
        today_checked = any(checkin.checkin_date == today for checkin in participation.checkins)
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
            today_missions=ChallengeService._build_today_missions(active_participations, today),
            weekly_activity=weekly_activity,
        )

    @staticmethod
    def _build_today_missions(
        participations: list[ChallengeParticipation],
        today: date,
    ) -> list[ChallengeTodayMissionResponse]:
        missions = []
        for participation in participations:
            today_checked = any(checkin.checkin_date == today for checkin in participation.checkins)
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
    def _completion_rate(progress_count: int, duration_days: int) -> float:
        if duration_days <= 0:
            return 0.0
        return round(min(progress_count / duration_days, 1.0) * 100, 1)
