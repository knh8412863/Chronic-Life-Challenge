from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, model_validator

from app.core.validators import validate_birthday, validate_password, validate_phone_number
from app.models.users import Gender


class SignUpRequest(BaseModel):
    email: Annotated[
        EmailStr,
        Field(None, max_length=40),
    ]
    password: Annotated[str, Field(min_length=8), AfterValidator(validate_password)]
    name: Annotated[str, Field(max_length=20)]
    gender: Gender
    birth_date: Annotated[date, AfterValidator(validate_birthday)]
    phone_number: Annotated[str, AfterValidator(validate_phone_number)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str


class TokenRefreshResponse(LoginResponse): ...


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: Annotated[str, Field(min_length=8), AfterValidator(validate_password)]
    new_password_confirm: str

    @model_validator(mode="after")
    def validate_password_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("비밀번호가 일치하지 않습니다.")
        return self
