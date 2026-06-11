from datetime import datetime

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]
