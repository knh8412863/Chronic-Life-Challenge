import pytest
from fastapi import HTTPException

from app.dtos.auth import SignUpAvailabilityRequest
from app.services.auth import AuthService


class FakeUserRepository:
    def __init__(self, *, email_exists: bool = False, phone_exists: bool = False) -> None:
        self.email_exists = email_exists
        self.phone_exists = phone_exists
        self.checked_phone_number = ""

    async def exists_by_email(self, email: str) -> bool:
        return self.email_exists

    async def exists_by_phone_number(self, phone_number: str) -> bool:
        self.checked_phone_number = phone_number
        return self.phone_exists


@pytest.mark.asyncio
async def test_signup_availability_normalizes_phone_number_before_duplicate_check():
    service = AuthService()
    fake_repo = FakeUserRepository()
    service.user_repo = fake_repo  # type: ignore[assignment]

    await service.check_signup_availability(
        SignUpAvailabilityRequest(email="new@example.com", phone_number="010-1234-5678")
    )

    assert fake_repo.checked_phone_number == "01012345678"


@pytest.mark.asyncio
async def test_signup_availability_rejects_duplicate_phone_number():
    service = AuthService()
    service.user_repo = FakeUserRepository(phone_exists=True)  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await service.check_signup_availability(
            SignUpAvailabilityRequest(email="new@example.com", phone_number="01012345678")
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "이미 사용중인 휴대폰 번호입니다."
