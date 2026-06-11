from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class WeeklyReportGenerateRequest(BaseModel):
    force_regenerate: bool = False


class WeeklyReportSourceSummaryResponse(BaseModel):
    health_survey_count: int
    lipid_obesity_record_count: int
    renal_record_count: int
    vital_record_count: int = 0
    activity_log_count: int = 0
    exercise_log_count: int = 0
    meal_log_count: int = 0
    prediction_count: int
    at_risk_prediction_count: int
    challenge_checkin_count: int


class WeeklyReportSummaryCardResponse(BaseModel):
    label: str
    value: str
    status: Literal["NORMAL", "CAUTION", "HIGH", "UNAVAILABLE"]
    description: str


class WeeklyReportMetricSummaryResponse(BaseModel):
    metric: str
    label: str
    value: str
    unit: str | None = None
    status: Literal["NORMAL", "CAUTION", "HIGH", "UNAVAILABLE"]
    description: str


class WeeklyReportTrendSummaryResponse(BaseModel):
    status: Literal["IMPROVED", "UNCHANGED", "WORSENED", "UNAVAILABLE"]
    message: str
    previous_week_report_id: int | None = None


class WeeklyReportChallengeSummaryResponse(BaseModel):
    checkin_count: int
    completion_rate: float
    status: Literal["ACHIEVED", "IN_PROGRESS", "UNAVAILABLE"]
    message: str


class WeeklyReportResponse(BaseModel):
    report_id: int
    week_start_date: date
    week_end_date: date
    status: Literal["AVAILABLE", "EMPTY", "FAILED"] = "AVAILABLE"
    source_summary: WeeklyReportSourceSummaryResponse
    summary_cards: list[WeeklyReportSummaryCardResponse]
    metric_summaries: list[WeeklyReportMetricSummaryResponse]
    trend_summary: WeeklyReportTrendSummaryResponse
    challenge_summary: WeeklyReportChallengeSummaryResponse
    report_text: str
    provider: str
    model_name: str
    generated: bool
    created_at: datetime
    source_type: Literal["RULE_BASED", "LLM"] = "RULE_BASED"


class CurrentWeeklyReportResponse(BaseModel):
    status: Literal["AVAILABLE", "EMPTY", "GENERATABLE"]
    week_start_date: date
    week_end_date: date
    report: WeeklyReportResponse | None = None
    empty_message: str | None = None


class WeeklyReportListItemResponse(BaseModel):
    report_id: int
    week_start_date: date
    week_end_date: date
    summary_text: str
    overall_status: Literal["NORMAL", "CAUTION", "HIGH", "UNAVAILABLE"]
    created_at: datetime


class WeeklyReportExportResponse(BaseModel):
    report_id: int
    file_name: str
    content_type: str
    content: str
    content_encoding: Literal["TEXT", "BASE64"] = "TEXT"
    emailed: bool = False
