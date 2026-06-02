from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.models.users import Gender
from app.services.users import UserManageService, _calculate_bmi, _joined_days


def test_calculate_bmi_rounds_to_two_decimals():
    assert _calculate_bmi(height_cm=175, weight_kg=72) == 23.51


def test_joined_days_counts_signup_day_as_one():
    assert _joined_days(date(2026, 6, 1), date(2026, 6, 3)) == 3
    assert _joined_days(date(2026, 6, 3), date(2026, 6, 3)) == 1


def test_user_info_response_combines_user_profile_and_latest_health():
    user = SimpleNamespace(
        id=1,
        name="홍길동",
        email="hong@example.com",
        phone_number="01012345678",
        birthday=date(1985, 3, 15),
        gender=Gender.MALE,
        profile_image_url="https://example.com/profile.png",
        created_at=datetime(2026, 1, 15, 10, 0),
    )
    profile = SimpleNamespace(height_cm=Decimal("175.00"), weight_kg=Decimal("72.00"), bmi=Decimal("23.51"))
    latest_health = SimpleNamespace(diagnosed_diseases=["HYPERTENSION", "DIABETES"])

    result = UserManageService._to_user_info_response(
        user=user,
        profile=profile,
        latest_health=latest_health,
        today=date(2026, 6, 3),
    )

    assert result.id == 1
    assert result.profile_image_url == "https://example.com/profile.png"
    assert result.height == 175.0
    assert result.weight == 72.0
    assert result.bmi == 23.51
    assert result.managed_diseases == ["HYPERTENSION", "DIABETES"]
    assert result.joined_days == 140
    assert result.membership_grade == "일반 회원"
    assert result.points == 0
    assert result.level == 1


def test_profile_update_payload_uses_existing_profile_value_when_one_metric_changes():
    user = SimpleNamespace(birthday=date(1990, 1, 1), gender=Gender.FEMALE)
    profile = SimpleNamespace(
        birth_date=date(1990, 1, 1),
        gender=Gender.FEMALE,
        height_cm=Decimal("160.00"),
        weight_kg=Decimal("55.00"),
    )
    data = SimpleNamespace(height=None, weight=60)

    payload = UserManageService._build_profile_update_payload(user=user, profile=profile, data=data)

    assert payload["height_cm"] == Decimal("160.0")
    assert payload["weight_kg"] == Decimal("60")
    assert payload["bmi"] == Decimal("23.44")
