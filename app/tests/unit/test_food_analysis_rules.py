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
