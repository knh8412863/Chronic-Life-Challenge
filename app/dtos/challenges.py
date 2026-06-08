from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class ChallengeParticipationStatus(StrEnum):
    JOINED = "JOINED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class ChallengeDisplayCategory(StrEnum):
    WALK = "WALK"
    WATER = "WATER"
    EXERCISE = "EXERCISE"
    SLEEP = "SLEEP"
    DIET = "DIET"
    COMPREHENSIVE = "COMPREHENSIVE"


class ChallengeSummaryResponse(BaseModel):
    challenge_id: int
    title: str
    description: str
    category: ChallengeDisplayCategory
    target_metric: str
    goal_value: int
    duration_days: int
    difficulty: str = "NORMAL"
    reward_points: int = 0
    participant_count: int = 0
    is_joined: bool = False
    today_checked: bool = False


class ChallengeDetailResponse(ChallengeSummaryResponse):
    average_completion_rate: float = 0.0
    how_to_join: list[str] = Field(default_factory=list)
    daily_mission_examples: list[str] = Field(default_factory=list)
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


class ChallengeCancelResponse(BaseModel):
    participation_id: int
    challenge_id: int
    status: ChallengeParticipationStatus
    canceled_at: datetime


class ChallengeBadgeItemResponse(BaseModel):
    badge_id: str
    badge_name: str
    badge_type: str
    is_earned: bool
    current_streak: int
    target_streak: int
    progress_rate: float
    earned_at: datetime | None = None


class ChallengeBadgeListResponse(BaseModel):
    earned_count: int
    total_completion_rate: float
    items: list[ChallengeBadgeItemResponse]
    recent_earned: list[ChallengeBadgeItemResponse]


class ChallengeLeaderboardItemResponse(BaseModel):
    rank: int
    user_id: int
    nickname_masked: str
    score: int
    completed_mission_count: int


class ChallengeLeaderboardMyRankResponse(BaseModel):
    rank: int | None = None
    score: int = 0
    completed_mission_count: int = 0


class ChallengeWeeklyLeaderboardResponse(BaseModel):
    week_start: date
    week_end: date
    top_three: list[ChallengeLeaderboardItemResponse]
    my_rank: ChallengeLeaderboardMyRankResponse
    items: list[ChallengeLeaderboardItemResponse]
