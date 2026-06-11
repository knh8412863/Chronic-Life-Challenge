from datetime import date, datetime

from pydantic import BaseModel


class DashboardRiskTrendItemResponse(BaseModel):
    result_id: int
    created_at: datetime
    overall_risk_level: str
    disease_risks: dict[str, float]


class DashboardRiskTrendResponse(BaseModel):
    items: list[DashboardRiskTrendItemResponse]


class DashboardChallengeCalendarItemResponse(BaseModel):
    activity_date: date
    completed_count: int


class DashboardChallengeCalendarResponse(BaseModel):
    items: list[DashboardChallengeCalendarItemResponse]


class DashboardKoreaComparisonItemResponse(BaseModel):
    metric: str
    user_value: float | None = None
    comparison_value: float | None = None
    unit: str | None = None
    message: str


class DashboardKoreaComparisonResponse(BaseModel):
    items: list[DashboardKoreaComparisonItemResponse]
