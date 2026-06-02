from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class WeeklyReportGenerateRequest(BaseModel):
    force_regenerate: bool = False


class WeeklyReportSourceSummaryResponse(BaseModel):
    health_survey_count: int
    lipid_obesity_record_count: int
    renal_record_count: int
    prediction_count: int
    at_risk_prediction_count: int
    challenge_checkin_count: int


class WeeklyReportResponse(BaseModel):
    report_id: int
    week_start_date: date
    week_end_date: date
    source_summary: WeeklyReportSourceSummaryResponse
    report_text: str
    provider: str
    model_name: str
    generated: bool
    created_at: datetime
    source_type: Literal["RULE_BASED", "LLM"] = "RULE_BASED"
