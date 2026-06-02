from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class AdviceTriggerType(StrEnum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


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
