from datetime import date, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.dtos.predictions import ExerciseLogCreateRequest, ExerciseType
from app.services.predictions import HealthInputService


def test_exercise_log_create_request_accepts_valid_exercise():
    request = ExerciseLogCreateRequest(
        exercise_date=date(2026, 6, 2),
        exercise_type=ExerciseType.WALKING,
        duration_minutes=30,
        calories_burned=120,
        memo="저녁 산책",
    )

    assert request.exercise_type == ExerciseType.WALKING
    assert request.duration_minutes == 30


def test_exercise_log_create_request_rejects_zero_duration():
    with pytest.raises(ValidationError):
        ExerciseLogCreateRequest(
            exercise_date=date(2026, 6, 2),
            exercise_type=ExerciseType.RUNNING,
            duration_minutes=0,
        )


def test_exercise_log_response_maps_type_and_values():
    now = datetime(2026, 6, 2, 20, 0)
    record = SimpleNamespace(
        id=7,
        exercise_date=date(2026, 6, 2),
        exercise_type="CYCLING",
        duration_minutes=45,
        calories_burned=300,
        memo=None,
        created_at=now,
        updated_at=now,
    )

    result = HealthInputService._to_exercise_log(record)

    assert result.exercise_log_id == 7
    assert result.exercise_type == ExerciseType.CYCLING
    assert result.duration_minutes == 45
    assert result.calories_burned == 300


def test_exercise_summary_sums_duration_and_calories():
    records = [
        SimpleNamespace(duration_minutes=30, calories_burned=120),
        SimpleNamespace(duration_minutes=45, calories_burned=None),
        SimpleNamespace(duration_minutes=20, calories_burned=80),
    ]

    summary = HealthInputService._build_exercise_summary(records)

    assert summary.total_duration_minutes == 95
    assert summary.total_calories_burned == 200
    assert summary.logged_count == 3


async def test_exercise_calories_are_estimated_from_met_when_empty(monkeypatch):
    async def fake_weight(_user):
        return 60

    monkeypatch.setattr(HealthInputService, "_exercise_weight_kg", fake_weight)

    result = await HealthInputService._resolve_exercise_calories(
        user=SimpleNamespace(gender="FEMALE"),
        exercise_type="WALKING",
        duration_minutes=30,
        calories_burned=None,
    )

    assert result == 105


async def test_exercise_calories_keep_manual_value(monkeypatch):
    async def fake_weight(_user):
        return 60

    monkeypatch.setattr(HealthInputService, "_exercise_weight_kg", fake_weight)

    result = await HealthInputService._resolve_exercise_calories(
        user=SimpleNamespace(gender="FEMALE"),
        exercise_type="WALKING",
        duration_minutes=30,
        calories_burned=88,
    )

    assert result == 88
