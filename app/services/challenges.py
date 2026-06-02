from datetime import date, timedelta

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.dtos.challenges import (
    ChallengeCheckinCreateRequest,
    ChallengeCheckinResponse,
    ChallengeDetailResponse,
    ChallengeJoinResponse,
    ChallengeParticipationStatus,
    ChallengeSummaryResponse,
    MyChallengeResponse,
)
from app.models.challenges import Challenge, ChallengeCheckin, ChallengeParticipation
from app.models.users import User


class ChallengeService:
    async def get_challenges(self, user: User) -> list[ChallengeSummaryResponse]:
        challenges = await Challenge.filter(is_active=True).order_by("id")
        active_participations = await ChallengeParticipation.filter(
            user_id=user.id,
            status=ChallengeParticipationStatus.JOINED.value,
        ).values_list("challenge_id", flat=True)
        joined_ids = set(active_participations)
        return [self._to_summary(challenge, challenge.id in joined_ids) for challenge in challenges]

    async def get_challenge(self, user: User, challenge_id: int) -> ChallengeDetailResponse:
        challenge = await self._get_active_challenge(challenge_id)
        is_joined = await ChallengeParticipation.exists(
            user_id=user.id,
            challenge_id=challenge.id,
            status=ChallengeParticipationStatus.JOINED.value,
        )
        return ChallengeDetailResponse(
            **self._to_summary(challenge, is_joined).model_dump(),
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

    @staticmethod
    async def _get_active_challenge(challenge_id: int) -> Challenge:
        challenge = await Challenge.get_or_none(id=challenge_id, is_active=True)
        if challenge is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="챌린지를 찾을 수 없습니다.")
        return challenge

    @staticmethod
    def _to_summary(challenge: Challenge, is_joined: bool) -> ChallengeSummaryResponse:
        return ChallengeSummaryResponse(
            challenge_id=challenge.id,
            title=challenge.title,
            description=challenge.description,
            category=challenge.category,
            target_metric=challenge.target_metric,
            goal_value=challenge.goal_value,
            duration_days=challenge.duration_days,
            is_joined=is_joined,
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
    def _completion_rate(progress_count: int, duration_days: int) -> float:
        if duration_days <= 0:
            return 0.0
        return round(min(progress_count / duration_days, 1.0) * 100, 1)
