from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AdviceTriggerType(StrEnum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class AdviceFeedbackType(StrEnum):
    HELPFUL = "HELPFUL"
    NOT_HELPFUL = "NOT_HELPFUL"


class AdviceGenerateRequest(BaseModel):
    trigger_type: AdviceTriggerType = AdviceTriggerType.MANUAL


class DailyAdviceResponse(BaseModel):
    advice_id: int
    advice_date: date
    title: str
    advice_text: str
    provider: str
    model_name: str
    trigger_type: AdviceTriggerType
    generated: bool
    created_at: datetime
    source_type: Literal["RULE_BASED", "LLM"] = "RULE_BASED"
    remaining_regeneration_count: int = 2


class AdviceHistoryItemResponse(BaseModel):
    advice_id: int
    advice_date: date
    title: str
    advice_text: str
    trigger_type: AdviceTriggerType
    source_type: Literal["RULE_BASED", "LLM"] = "RULE_BASED"
    feedback_type: AdviceFeedbackType | None = None
    created_at: datetime


class AdviceFeedbackCreateRequest(BaseModel):
    feedback_type: AdviceFeedbackType
    comment: Annotated[str | None, Field(default=None, max_length=500)]


class AdviceFeedbackCreateResponse(BaseModel):
    feedback_id: int
    advice_id: int
    feedback_type: AdviceFeedbackType
    created_at: datetime
