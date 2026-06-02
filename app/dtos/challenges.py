from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class ChallengeParticipationStatus(StrEnum):
    JOINED = "JOINED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class ChallengeSummaryResponse(BaseModel):
    challenge_id: int
    title: str
    description: str
    category: str
    target_metric: str
    goal_value: int
    duration_days: int
    is_joined: bool = False


class ChallengeDetailResponse(ChallengeSummaryResponse):
    created_at: datetime
    updated_at: datetime


class ChallengeJoinResponse(BaseModel):
    participation_id: int
    challenge_id: int
    status: ChallengeParticipationStatus
    start_date: date
    end_date: date
    progress_count: int
    completion_rate: float
    created_at: datetime


class MyChallengeResponse(BaseModel):
    participation_id: int
    challenge_id: int
    title: str
    status: ChallengeParticipationStatus
    start_date: date
    end_date: date
    progress_count: int
    duration_days: int
    completion_rate: float
    today_checked: bool


class ChallengeTodayMissionResponse(BaseModel):
    participation_id: int
    challenge_id: int
    title: str
    mission_text: str
    today_checked: bool


class ChallengeWeeklyActivityResponse(BaseModel):
    activity_date: date
    completed_count: int


class ChallengeDashboardSummaryResponse(BaseModel):
    active_count: int
    completed_count: int
    weekly_completion_rate: float
    current_streak_days: int
    completed_mission_count: int
    earned_badge_count: int = 0
    today_missions: list[ChallengeTodayMissionResponse]
    weekly_activity: list[ChallengeWeeklyActivityResponse]


class ChallengeCheckinCreateRequest(BaseModel):
    note: Annotated[str | None, Field(default=None, max_length=255)]


class ChallengeCheckinResponse(BaseModel):
    checkin_id: int
    participation_id: int
    checkin_date: date
    progress_count: int
    status: ChallengeParticipationStatus
    completion_rate: float
    created_at: datetime
