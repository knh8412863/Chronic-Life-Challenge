from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.dtos.predictions import MealLogCreateRequest, MealType
from app.services.predictions import HealthInputService


def test_meal_log_create_request_accepts_manual_nutrition_values():
    request = MealLogCreateRequest(
        meal_date=date(2026, 6, 2),
        meal_type=MealType.LUNCH,
        food_name="닭가슴살 샐러드",
        amount="1인분",
        calories=420,
        carbs_g=35.5,
        protein_g=31.2,
        fat_g=12.4,
        sodium_mg=680,
        sugar_g=6.1,
        fiber_g=4.3,
        memo="점심",
    )

    assert request.meal_type == MealType.LUNCH
    assert request.food_analysis_result_id is None
    assert request.fiber_g == 4.3


def test_meal_log_create_request_rejects_negative_nutrition_values():
    with pytest.raises(ValidationError):
        MealLogCreateRequest(
            meal_date=date(2026, 6, 2),
            meal_type=MealType.DINNER,
            food_name="저녁",
            calories=-1,
        )


def test_meal_log_response_converts_decimal_nutrition_to_float():
    now = datetime(2026, 6, 2, 12, 0, 0)
    record = SimpleNamespace(
        id=10,
        food_analysis_result_id=3,
        meal_date=date(2026, 6, 2),
        meal_type="BREAKFAST",
        food_name="오트밀",
        amount="1그릇",
        calories=330,
        carbs_g=Decimal("42.50"),
        protein_g=Decimal("12.25"),
        fat_g=Decimal("8.10"),
        sodium_mg=Decimal("220.00"),
        sugar_g=Decimal("5.50"),
        fiber_g=Decimal("6.00"),
        memo=None,
        created_at=now,
        updated_at=now,
    )

    result = HealthInputService._to_meal_log(record)

    assert result.meal_log_id == 10
    assert result.meal_type == MealType.BREAKFAST
    assert result.carbs_g == 42.5
    assert result.sodium_mg == 220.0
    assert result.fiber_g == 6.0


def test_meal_daily_summary_groups_by_date_and_sums_nutrition_values():
    records = [
        SimpleNamespace(
            meal_date=date(2026, 6, 2),
            calories=300,
            sodium_mg=Decimal("500.50"),
            sugar_g=Decimal("8.20"),
            fiber_g=Decimal("2.00"),
        ),
        SimpleNamespace(
            meal_date=date(2026, 6, 2),
            calories=None,
            sodium_mg=None,
            sugar_g=Decimal("1.30"),
            fiber_g=Decimal("3.00"),
        ),
        SimpleNamespace(
            meal_date=date(2026, 6, 1),
            calories=700,
            sodium_mg=Decimal("1000.00"),
            sugar_g=None,
            fiber_g=None,
        ),
    ]

    result = HealthInputService._build_meal_daily_summary(records)

    assert [item.meal_date for item in result] == [date(2026, 6, 2), date(2026, 6, 1)]
    assert result[0].meal_count == 2
    assert result[0].total_calories == 300
    assert result[0].total_sodium_mg == 500.5
    assert result[0].total_sugar_g == 9.5
    assert result[0].total_fiber_g == 5.0
