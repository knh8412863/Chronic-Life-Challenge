from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.dtos.predictions import MetricAssessmentItemResponse


class HomeHealthScoreResponse(BaseModel):
    score: int | None
    status: Literal["GOOD", "CAUTION", "HIGH", "NEEDS_INPUT"]
    message: str
    calculation_basis: list[str] = Field(default_factory=list)


class HomeRecentPredictionResponse(BaseModel):
    result_id: int
    overall_risk_level: str
    at_risk_diseases: list[str] = Field(default_factory=list)
    created_at: datetime


class HomeTodayAdviceResponse(BaseModel):
    advice_id: int | None = None
    title: str
    content: str
    is_placeholder: bool = True


class HomeChallengeSummaryResponse(BaseModel):
    active_count: int = 0
    completion_rate: float = 0.0
    message: str


class HomeHealthRecordStatusResponse(BaseModel):
    has_health_survey: bool
    has_lipid_obesity_record: bool
    has_renal_record: bool
    latest_health_input_at: datetime | None = None
    latest_lipid_obesity_record_at: datetime | None = None
    latest_renal_record_at: datetime | None = None


class HomeHealthMetricSummaryResponse(BaseModel):
    dyslipidemia: MetricAssessmentItemResponse
    obesity: MetricAssessmentItemResponse


class HomeVitalSummaryResponse(BaseModel):
    blood_pressure_label: str
    blood_pressure_status: Literal["NORMAL", "CAUTION", "HIGH", "NEEDS_INPUT"]
    blood_pressure_value: str | None = None
    glucose_label: str
    glucose_status: Literal["NORMAL", "CAUTION", "HIGH", "NEEDS_INPUT"]
    glucose_value: str | None = None
    has_today_health_record: bool = False


class HomeSummaryResponse(BaseModel):
    today_score: HomeHealthScoreResponse
    recent_prediction: HomeRecentPredictionResponse | None
    today_advice: HomeTodayAdviceResponse
    challenge_summary: HomeChallengeSummaryResponse
    health_metric_summary: HomeHealthMetricSummaryResponse
    vital_summary: HomeVitalSummaryResponse
    quick_record_status: HomeHealthRecordStatusResponse
    unread_notification_count: int = 0
