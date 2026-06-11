from datetime import date
from typing import Literal

from pydantic import BaseModel


class HealthScoreResponse(BaseModel):
    score_date: date
    total_score: int | None
    grade: str | None
    status: Literal["GOOD", "CAUTION", "HIGH", "NEEDS_INPUT"]
    message: str
    calculation_basis: list[str]


class HealthScoreHistoryResponse(BaseModel):
    items: list[HealthScoreResponse]
