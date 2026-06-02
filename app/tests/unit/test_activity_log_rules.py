from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.dtos.predictions import ActivityLogCreateRequest
from app.services.predictions import HealthInputService


def test_activity_log_create_request_requires_at_least_one_value():
    with pytest.raises(ValidationError):
        ActivityLogCreateRequest(record_date=date(2026, 6, 2))


def test_activity_log_create_request_validates_alcohol_amount_when_not_drinking():
    with pytest.raises(ValidationError):
        ActivityLogCreateRequest(
            record_date=date(2026, 6, 2),
            alcohol_frequency=0,
            alcohol_amount=2,
        )


def test_activity_log_create_request_requires_alcohol_amount_when_drinking():
    with pytest.raises(ValidationError):
        ActivityLogCreateRequest(
            record_date=date(2026, 6, 2),
            alcohol_frequency=1,
        )


def test_activity_summary_averages_available_values():
    records = [
        SimpleNamespace(
            walking_days=5,
            sedentary_hours=Decimal("8.0"),
            sleep_hours=Decimal("7.0"),
            stress_level=2,
            diet_score=Decimal("8.0"),
        ),
        SimpleNamespace(
            walking_days=3,
            sedentary_hours=Decimal("10.0"),
            sleep_hours=Decimal("6.0"),
            stress_level=4,
            diet_score=Decimal("6.0"),
        ),
    ]

    summary = HealthInputService._build_activity_summary(records)

    assert summary.avg_walking_days == 4.0
    assert summary.avg_sedentary_hours == 9.0
    assert summary.avg_sleep_hours == 6.5
    assert summary.avg_stress_level == 3.0
    assert summary.avg_diet_score == 7.0
    assert summary.logged_days == 2


def test_activity_log_response_converts_decimal_values():
    now = datetime(2026, 6, 2, 9, 0)
    record = SimpleNamespace(
        id=4,
        record_date=date(2026, 6, 2),
        alcohol_frequency=1,
        alcohol_amount=2,
        walking_days=5,
        sedentary_hours=Decimal("8.5"),
        sleep_hours=Decimal("7.0"),
        stress_level=2,
        diet_score=Decimal("8.5"),
        memo="좋음",
        created_at=now,
        updated_at=now,
    )

    result = HealthInputService._to_activity_log(record)

    assert result.activity_log_id == 4
    assert result.sedentary_hours == 8.5
    assert result.sleep_hours == 7.0
    assert result.diet_score == 8.5
