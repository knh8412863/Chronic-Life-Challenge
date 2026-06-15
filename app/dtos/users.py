from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.core.validators import optional_after_validator, validate_password, validate_phone_number
from app.dtos.base import BaseSerializerModel
from app.models.users import Gender, WithdrawalReason


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


class ConsentUpdateRequest(BaseModel):
    is_agreed: bool
    policy_version: str = "v1.0"


class UserConsentItemResponse(BaseModel):
    consent_type: str
    title: str
    is_required: bool
    is_agreed: bool
    agreed_at: datetime | None = None
    withdrawn_at: datetime | None = None
    policy_version: str


class PolicyChangeResponse(BaseModel):
    policy_type: str
    title: str
    policy_version: str
    changed_at: date | None = None


class UserConsentListResponse(BaseModel):
    items: list[UserConsentItemResponse]
    recent_policy_changes: list[PolicyChangeResponse] = Field(default_factory=list)


class PolicyDocumentResponse(BaseModel):
    policy_type: str
    title: str
    policy_version: str
    changed_at: date | None = None
    content: str


class UserWithdrawalRequest(BaseModel):
    password: Annotated[str, Field(min_length=8, max_length=128)]
    withdrawal_reason: WithdrawalReason
    withdrawal_comment: Annotated[str | None, Field(None, max_length=500)] = None
    confirm_agreed: bool


class UserPasswordVerificationRequest(BaseModel):
    password: Annotated[str, Field(min_length=8, max_length=128)]


class UserEmailChangeRequest(BaseModel):
    new_email: EmailStr


class UserEmailChangeConfirmRequest(BaseModel):
    token: Annotated[str, Field(min_length=20)]


class PasswordChangeRequest(BaseModel):
    current_password: Annotated[str, Field(min_length=8, max_length=128)]
    new_password: Annotated[str, Field(min_length=8, max_length=128), optional_after_validator(validate_password)]
    new_password_confirm: Annotated[str, Field(min_length=8, max_length=128)]

    def model_post_init(self, __context) -> None:
        if self.new_password != self.new_password_confirm:
            raise ValueError("비밀번호가 일치하지 않습니다.")
