from datetime import date

import pytest
from pydantic import ValidationError

from app.dtos.auth import PasswordResetConfirmRequest, SignUpRequest
from app.dtos.predictions import HealthSurveyCreateRequest, LipidObesityRecordCreateRequest


def test_signup_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        SignUpRequest(
            email="invalid-email",
            password="Password123!",
            name="테스터",
            gender="MALE",
            birth_date=date(1990, 1, 1),
            phone_number="01012345678",
        )


def test_signup_request_requires_required_consents():
    with pytest.raises(ValidationError) as exc_info:
        SignUpRequest(
            email="test@example.com",
            password="Password123!",
            name="테스터",
            gender="MALE",
            birth_date=date(1990, 1, 1),
            phone_number="01012345678",
            consent_privacy_agreed=False,
        )

    assert "필수 약관 동의가 필요합니다." in str(exc_info.value)


def test_password_reset_request_rejects_password_mismatch():
    with pytest.raises(ValidationError) as exc_info:
        PasswordResetConfirmRequest(
            token="reset-token",
            new_password="NewPassword123!",
            new_password_confirm="Mismatch123!",
        )

    assert "비밀번호가 일치하지 않습니다." in str(exc_info.value)


def test_health_survey_requires_alcohol_amount_when_user_drinks():
    with pytest.raises(ValidationError) as exc_info:
        HealthSurveyCreateRequest(
            birth_date=date(1990, 1, 1),
            height=165,
            weight=63,
            smoking_status=0,
            alcohol_frequency=1,
            exercise_frequency=3,
        )

    assert "alcohol_amount is required" in str(exc_info.value)


def test_health_survey_rejects_alcohol_amount_when_user_does_not_drink():
    with pytest.raises(ValidationError) as exc_info:
        HealthSurveyCreateRequest(
            birth_date=date(1990, 1, 1),
            height=165,
            weight=63,
            smoking_status=0,
            alcohol_frequency=0,
            alcohol_amount=1,
            exercise_frequency=3,
        )

    assert "alcohol_amount must be empty" in str(exc_info.value)


def test_lipid_obesity_record_requires_at_least_one_measurement():
    with pytest.raises(ValidationError) as exc_info:
        LipidObesityRecordCreateRequest(record_date=date(2026, 6, 4))

    assert "At least one lipid or obesity measurement is required." in str(exc_info.value)


def test_lipid_obesity_record_requires_height_and_weight_together():
    with pytest.raises(ValidationError) as exc_info:
        LipidObesityRecordCreateRequest(record_date=date(2026, 6, 4), height=165)

    assert "height and weight must be submitted together" in str(exc_info.value)
