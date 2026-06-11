from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.dtos.foods import FoodAnalysisRequest
from app.dtos.predictions import MealType
from app.models.foods import FoodAnalysisStatus
from app.services.foods import FoodAnalysisService


def test_food_analysis_rules_detect_high_sodium_and_sugar():
    request = FoodAnalysisRequest(
        meal_date=date(2026, 6, 2),
        meal_type=MealType.LUNCH,
        food_name="라면",
        amount="1봉",
        calories=520,
        sodium_mg=1800,
        sugar_g=30,
        protein_g=8,
        fiber_g=1,
    )

    score, risk_flags, advice_text = FoodAnalysisService._analyze_nutrition(request)

    assert score == 50
    assert "HIGH_SODIUM" in risk_flags
    assert "HIGH_SUGAR" in risk_flags
    assert "LOW_PROTEIN" in risk_flags
    assert "LOW_FIBER" in risk_flags
    assert "나트륨이 높은 편" in advice_text


def test_food_analysis_rules_returns_no_risk_for_balanced_input():
    request = FoodAnalysisRequest(
        food_name="현미밥 닭가슴살 샐러드",
        calories=450,
        sodium_mg=500,
        sugar_g=5,
        fat_g=12,
        protein_g=30,
        fiber_g=6,
    )

    score, risk_flags, advice_text = FoodAnalysisService._analyze_nutrition(request)

    assert score == 100
    assert risk_flags == []
    assert "큰 위험 신호는 없습니다" in advice_text


def test_food_analysis_status_supports_job_lifecycle_values():
    assert FoodAnalysisStatus.PENDING == "PENDING"
    assert FoodAnalysisStatus.RUNNING == "RUNNING"
    assert FoodAnalysisStatus.SUCCESS == "SUCCESS"
    assert FoodAnalysisStatus.FAILED == "FAILED"


def test_food_analysis_manual_key_is_scoped_by_user_and_task_uuid():
    user = SimpleNamespace(id=42)

    key = FoodAnalysisService._build_manual_analysis_key(user, "task-uuid")

    assert key == "manual-food-analyses/user-42/task-uuid.json"


def test_food_analysis_response_converts_decimal_nutrition_values():
    now = datetime(2026, 6, 2, 18, 0, 0)
    result = SimpleNamespace(
        id=7,
        task_uuid="task-uuid",
        status=FoodAnalysisStatus.SUCCESS,
        meal_date=date(2026, 6, 2),
        meal_type="DINNER",
        food_name="비빔밥",
        amount="1그릇",
        calories=650,
        carbs_g=Decimal("80.50"),
        protein_g=Decimal("22.00"),
        fat_g=Decimal("18.30"),
        sodium_mg=Decimal("1200.00"),
        sugar_g=Decimal("9.20"),
        fiber_g=Decimal("5.00"),
        health_score=90,
        risk_flags=["HIGH_SODIUM"],
        advice_text="나트륨을 조절해 보세요.",
        created_at=now,
    )

    response = FoodAnalysisService._to_response(result)

    assert response.food_analysis_result_id == 7
    assert response.meal_type == MealType.DINNER
    assert response.nutrition.carbs_g == 80.5
    assert response.nutrition.sodium_mg == 1200.0
    assert response.risk_flags == ["HIGH_SODIUM"]


def test_meal_summary_sums_nutrition_values():
    meals = [
        SimpleNamespace(
            calories=500,
            sodium_mg=Decimal("800.50"),
            sugar_g=Decimal("8.00"),
            fiber_g=Decimal("4.00"),
            protein_g=Decimal("20.50"),
        ),
        SimpleNamespace(
            calories=None,
            sodium_mg=None,
            sugar_g=Decimal("2.30"),
            fiber_g=None,
            protein_g=Decimal("5.00"),
        ),
    ]

    result = FoodAnalysisService._build_meal_summary(meals)

    assert result.meal_count == 2
    assert result.total_calories == 500
    assert result.total_sodium_mg == 800.5
    assert result.total_sugar_g == 10.3
    assert result.total_fiber_g == 4.0
    assert result.total_protein_g == 25.5


def test_daily_summaries_group_meals_by_date_descending():
    meals = [
        SimpleNamespace(
            meal_date=date(2026, 6, 1),
            calories=300,
            sodium_mg=Decimal("500.00"),
            sugar_g=None,
            fiber_g=None,
            protein_g=Decimal("10.00"),
        ),
        SimpleNamespace(
            meal_date=date(2026, 6, 2),
            calories=700,
            sodium_mg=Decimal("900.00"),
            sugar_g=Decimal("5.00"),
            fiber_g=Decimal("3.00"),
            protein_g=Decimal("30.00"),
        ),
    ]

    result = FoodAnalysisService._build_daily_summaries(meals)

    assert [item.meal_date for item in result] == [date(2026, 6, 2), date(2026, 6, 1)]
    assert result[0].nutrition_summary.total_calories == 700
    assert result[1].nutrition_summary.total_protein_g == 10.0


def test_latest_analysis_advice_response_uses_analysis_fields():
    now = datetime(2026, 6, 2, 19, 0, 0)
    result = SimpleNamespace(
        id=3,
        task_uuid="task-3",
        food_name="김치찌개",
        health_score=75,
        risk_flags=["HIGH_SODIUM"],
        advice_text="나트륨 조절이 필요합니다.",
        created_at=now,
    )

    response = FoodAnalysisService._to_latest_analysis_advice(result)

    assert response.food_analysis_result_id == 3
    assert response.food_name == "김치찌개"
    assert response.risk_flags == ["HIGH_SODIUM"]
    assert response.created_at == now
