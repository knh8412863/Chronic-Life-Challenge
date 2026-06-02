from types import SimpleNamespace

from app.dtos.predictions import ActivityLogSummaryResponse, ExerciseLogSummaryResponse
from app.services.predictions import HealthInputService


def test_progress_rate_caps_at_one_hundred_percent():
    assert HealthInputService._progress_rate(150, 100) == 100.0
    assert HealthInputService._progress_rate(30, 100) == 30.0


def test_progress_rate_returns_none_when_target_is_missing_or_zero():
    assert HealthInputService._progress_rate(10, None) is None
    assert HealthInputService._progress_rate(None, 10) is None
    assert HealthInputService._progress_rate(10, 0) is None


def test_progress_status_maps_rate_to_status():
    assert HealthInputService._progress_status(None) == "UNAVAILABLE"
    assert HealthInputService._progress_status(99.9) == "IN_PROGRESS"
    assert HealthInputService._progress_status(100.0) == "ACHIEVED"


def test_goal_progress_uses_period_days_for_exercise_target():
    lifestyle_goal = SimpleNamespace(
        target_exercise_minutes=30,
        target_sleep_hours=None,
        target_diet_score=None,
    )
    activity_summary = ActivityLogSummaryResponse(
        avg_walking_days=None,
        avg_sedentary_hours=None,
        avg_sleep_hours=None,
        avg_stress_level=None,
        avg_diet_score=None,
        logged_days=0,
    )
    exercise_summary = ExerciseLogSummaryResponse(
        total_duration_minutes=90,
        total_calories_burned=300,
        logged_count=3,
    )

    result = HealthInputService._build_goal_progress(
        lifestyle_goal=lifestyle_goal,
        activity_summary=activity_summary,
        exercise_summary=exercise_summary,
        period_days=7,
    )

    exercise_progress = result[0]
    assert exercise_progress.metric == "EXERCISE_MINUTES"
    assert exercise_progress.current_value == 90.0
    assert exercise_progress.target_value == 210.0
    assert exercise_progress.progress_rate == 42.9
    assert exercise_progress.status == "IN_PROGRESS"


def test_goal_progress_marks_missing_optional_targets_unavailable():
    lifestyle_goal = SimpleNamespace(
        target_exercise_minutes=30,
        target_sleep_hours=None,
        target_diet_score=None,
    )
    activity_summary = ActivityLogSummaryResponse(
        avg_walking_days=None,
        avg_sedentary_hours=None,
        avg_sleep_hours=7.0,
        avg_stress_level=None,
        avg_diet_score=8.0,
        logged_days=2,
    )
    exercise_summary = ExerciseLogSummaryResponse(total_duration_minutes=0, total_calories_burned=0, logged_count=0)

    result = HealthInputService._build_goal_progress(
        lifestyle_goal=lifestyle_goal,
        activity_summary=activity_summary,
        exercise_summary=exercise_summary,
        period_days=1,
    )

    assert result[1].metric == "SLEEP_HOURS"
    assert result[1].status == "UNAVAILABLE"
    assert result[2].metric == "DIET_SCORE"
    assert result[2].status == "UNAVAILABLE"
