from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.core.validators import optional_after_validator, validate_phone_number
from app.dtos.base import BaseSerializerModel
from app.models.users import Gender


class UserUpdateRequest(BaseModel):
    name: Annotated[str | None, Field(None, min_length=2, max_length=20)]
    phone_number: Annotated[
        str | None,
        Field(None, description="Available Format: +8201011112222, 01011112222, 010-1111-2222"),
        optional_after_validator(validate_phone_number),
    ]
    height: Annotated[float | None, Field(None, ge=100, le=250)]
    weight: Annotated[float | None, Field(None, ge=20, le=300)]
    profile_image_url: Annotated[str | None, Field(None, max_length=500)]
    managed_diseases: Annotated[list[str] | None, Field(None, max_length=5)]


class UserInfoResponse(BaseSerializerModel):
    id: int
    name: str
    email: str
    phone_number: str
    birthday: date
    gender: Gender
    profile_image_url: str | None = None
    height: float | None = None
    weight: float | None = None
    bmi: float | None = None
    managed_diseases: list[str] = Field(default_factory=list)
    joined_days: int
    membership_grade: str = "일반 회원"
    points: int = 0
    level: int = 1
    created_at: datetime
