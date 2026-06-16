import pytest
from fastapi import HTTPException

from app.dtos.users import UserWithdrawalRequest
from app.models.users import WithdrawalReason
from app.services.users import UserManageService


def test_withdrawal_payload_trims_optional_comment():
    request = UserWithdrawalRequest(
        password="password123",
        withdrawal_reason=WithdrawalReason.OTHER,
        withdrawal_comment="  사용 빈도가 낮아요.  ",
        confirm_agreed=True,
    )

    payload = UserManageService._build_withdrawal_payload(request)

    assert payload == {
        "withdrawal_reason": WithdrawalReason.OTHER,
        "withdrawal_comment": "사용 빈도가 낮아요.",
        "confirm_agreed": True,
    }


def test_withdrawal_payload_keeps_empty_comment_as_none():
    request = UserWithdrawalRequest(
        password="password123",
        withdrawal_reason=WithdrawalReason.NOT_USEFUL,
        withdrawal_comment=None,
        confirm_agreed=True,
    )

    payload = UserManageService._build_withdrawal_payload(request)

    assert payload["withdrawal_comment"] is None


def test_withdrawal_requires_user_confirmation():
    with pytest.raises(HTTPException) as exc_info:
        UserManageService._validate_withdrawal_agreement(False)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "탈퇴 유의사항에 동의해주세요."


def test_withdrawn_user_payload_anonymizes_identifiers():
    payload = UserManageService._build_withdrawn_user_payload(123)

    assert payload == {
        "email": "withdrawn_123@all4health.deleted",
        "phone_number": "WD000000123",
        "google_sub": None,
        "profile_image_url": None,
        "is_active": False,
    }
