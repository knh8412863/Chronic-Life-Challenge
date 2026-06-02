from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.dtos.predictions import HealthGoalUpdateRequest
from app.services.predictions import DEFAULT_LIFESTYLE_GOAL, HealthInputService


def test_default_lifestyle_goal_matches_service_policy():
    assert DEFAULT_LIFESTYLE_GOAL == {
        "target_steps": 10000,
        "target_water_ml": 2000,
        "target_exercise_minutes": 30,
        "target_sleep_hours": None,
        "target_diet_score": None,
    }


def test_health_goal_update_request_accepts_partial_sections():
    request = HealthGoalUpdateRequest(
        lifestyle_goal={
            "target_steps": 8000,
            "target_sleep_hours": 7.5,
        }
    )

    assert request.chronic_disease_goal is None
    assert request.lifestyle_goal.target_steps == 8000
    assert request.lifestyle_goal.target_sleep_hours == 7.5


def test_chronic_disease_goal_response_converts_decimal_values():
    now = datetime(2026, 6, 2, 10, 0)
    goal = SimpleNamespace(
        target_systolic_bp=120,
        target_diastolic_bp=80,
        target_fasting_glucose=100,
        target_postprandial_glucose=140,
        target_hba1c=Decimal("6.50"),
        target_ldl_cholesterol=100,
        target_hdl_cholesterol=50,
        target_triglycerides=150,
        target_bmi=Decimal("23.00"),
        target_weight_kg=Decimal("60.50"),
        target_egfr=Decimal("90.00"),
        updated_at=now,
    )

    result = HealthInputService._to_chronic_disease_goal(goal)

    assert result.target_hba1c == 6.5
    assert result.target_bmi == 23.0
    assert result.target_weight_kg == 60.5
    assert result.target_egfr == 90.0


def test_lifestyle_goal_response_converts_decimal_values():
    now = datetime(2026, 6, 2, 10, 0)
    goal = SimpleNamespace(
        target_steps=10000,
        target_water_ml=2000,
        target_exercise_minutes=30,
        target_sleep_hours=Decimal("7.5"),
        target_diet_score=Decimal("8.0"),
        updated_at=now,
    )

    result = HealthInputService._to_lifestyle_goal(goal)

    assert result.target_steps == 10000
    assert result.target_sleep_hours == 7.5
    assert result.target_diet_score == 8.0


def test_decimal_goal_fields_include_chronic_and_lifestyle_decimal_targets():
    fields = HealthInputService._decimal_goal_fields()

    assert "target_hba1c" in fields
    assert "target_weight_kg" in fields
    assert "target_sleep_hours" in fields
    assert "target_diet_score" in fields
