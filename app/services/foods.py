import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status

from app.core import config
from app.dtos.foods import (
    FoodAnalysisRequest,
    FoodAnalysisResponse,
    FoodDailyMealSummaryResponse,
    FoodNutritionResponse,
    FoodPeriodMealSummaryResponse,
    FoodTodayMealSummaryResponse,
    LatestFoodAnalysisAdviceResponse,
    MealNutritionSummaryResponse,
)
from app.dtos.predictions import MealType
from app.models.foods import FoodAnalysisResult
from app.models.predictions import MealLog
from app.models.users import User

MAX_ADVICE_LENGTH = 500


class FoodAnalysisService:
    async def analyze(self, user: User, data: FoodAnalysisRequest) -> FoodAnalysisResponse:
        score, risk_flags, advice_text = self._analyze_nutrition(data)
        result = await FoodAnalysisResult.create(
            user=user,
            task_uuid=str(uuid.uuid4()),
            meal_date=data.meal_date,
            meal_type=data.meal_type.value if data.meal_type else None,
            food_name=data.food_name,
            amount=data.amount,
            calories=data.calories,
            carbs_g=self._optional_decimal(data.carbs_g),
            protein_g=self._optional_decimal(data.protein_g),
            fat_g=self._optional_decimal(data.fat_g),
            sodium_mg=self._optional_decimal(data.sodium_mg),
            sugar_g=self._optional_decimal(data.sugar_g),
            fiber_g=self._optional_decimal(data.fiber_g),
            health_score=score,
            risk_flags=risk_flags,
            advice_text=advice_text,
        )
        return self._to_response(result)

    async def get_result(self, user: User, task_uuid: str) -> FoodAnalysisResponse:
        result = await FoodAnalysisResult.get_or_none(task_uuid=task_uuid, user_id=user.id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="식단 분석 결과를 찾을 수 없습니다.")
        return self._to_response(result)

    async def get_today_meal_summary(self, user: User) -> FoodTodayMealSummaryResponse:
        today = self._today()
        meals = await MealLog.filter(user_id=user.id, meal_date=today).order_by("-id").limit(100)
        latest_analysis = await FoodAnalysisResult.filter(user_id=user.id).order_by("-created_at").first()
        return FoodTodayMealSummaryResponse(
            summary_date=today,
            nutrition_summary=self._build_meal_summary(meals),
            latest_analysis_advice=self._to_latest_analysis_advice(latest_analysis) if latest_analysis else None,
        )

    async def get_period_meal_summary(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> FoodPeriodMealSummaryResponse:
        period_end = to_date or self._today()
        period_start = from_date or (period_end - timedelta(days=6))
        if period_start > period_end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="조회 시작일은 종료일보다 늦을 수 없습니다."
            )

        meals = (
            await MealLog.filter(user_id=user.id, meal_date__gte=period_start, meal_date__lte=period_end)
            .order_by("-meal_date", "-id")
            .limit(500)
        )
        return FoodPeriodMealSummaryResponse(
            period_start=period_start,
            period_end=period_end,
            daily_summaries=self._build_daily_summaries(meals),
        )

    @staticmethod
    def _analyze_nutrition(data: FoodAnalysisRequest) -> tuple[int, list[str], str]:
        score = 100
        risk_flags: list[str] = []
        advice_parts: list[str] = []

        if data.calories is not None and data.calories >= 800:
            score -= 15
            risk_flags.append("HIGH_CALORIES")
            advice_parts.append("열량이 높은 편이라 다음 끼니는 채소와 단백질 중심으로 가볍게 구성해 보세요.")
        if data.sodium_mg is not None and data.sodium_mg >= 1500:
            score -= 20
            risk_flags.append("HIGH_SODIUM")
            advice_parts.append("나트륨이 높은 편이므로 국물 섭취를 줄이고 물을 충분히 마시는 것이 좋습니다.")
        if data.sugar_g is not None and data.sugar_g >= 25:
            score -= 15
            risk_flags.append("HIGH_SUGAR")
            advice_parts.append("당류가 높은 편이라 단 음료나 간식은 줄이는 방향을 권장합니다.")
        if data.fat_g is not None and data.fat_g >= 30:
            score -= 10
            risk_flags.append("HIGH_FAT")
            advice_parts.append("지방 섭취가 높은 편이므로 튀김이나 가공식품 빈도를 조절해 보세요.")
        if data.protein_g is not None and data.protein_g < 10:
            score -= 10
            risk_flags.append("LOW_PROTEIN")
            advice_parts.append("단백질이 부족한 편이라 달걀, 두부, 생선, 살코기 등을 함께 고려해 보세요.")
        if data.fiber_g is not None and data.fiber_g < 3:
            score -= 5
            risk_flags.append("LOW_FIBER")
            advice_parts.append("식이섬유 보완을 위해 채소, 해조류, 통곡물을 추가하면 좋습니다.")

        if not risk_flags:
            advice_parts.append(
                "입력된 영양성분 기준으로 큰 위험 신호는 없습니다. 현재 식사 패턴을 꾸준히 기록해 보세요."
            )

        score = max(score, 0)
        advice_parts.append("본 분석은 의료 진단이 아닌 식단 관리 참고용입니다.")
        return score, risk_flags, FoodAnalysisService._limit_text(" ".join(advice_parts), MAX_ADVICE_LENGTH)

    @staticmethod
    def _to_response(result: FoodAnalysisResult) -> FoodAnalysisResponse:
        return FoodAnalysisResponse(
            food_analysis_result_id=result.id,
            task_uuid=result.task_uuid,
            status=result.status.value,
            meal_date=result.meal_date,
            meal_type=MealType(result.meal_type) if result.meal_type else None,
            food_name=result.food_name,
            amount=result.amount,
            nutrition=FoodNutritionResponse(
                calories=result.calories,
                carbs_g=FoodAnalysisService._optional_float(result.carbs_g),
                protein_g=FoodAnalysisService._optional_float(result.protein_g),
                fat_g=FoodAnalysisService._optional_float(result.fat_g),
                sodium_mg=FoodAnalysisService._optional_float(result.sodium_mg),
                sugar_g=FoodAnalysisService._optional_float(result.sugar_g),
                fiber_g=FoodAnalysisService._optional_float(result.fiber_g),
            ),
            health_score=result.health_score,
            risk_flags=result.risk_flags or [],
            advice_text=result.advice_text,
            created_at=result.created_at,
        )

    @staticmethod
    def _to_latest_analysis_advice(result: FoodAnalysisResult) -> LatestFoodAnalysisAdviceResponse:
        return LatestFoodAnalysisAdviceResponse(
            food_analysis_result_id=result.id,
            task_uuid=result.task_uuid,
            food_name=result.food_name,
            health_score=result.health_score,
            risk_flags=result.risk_flags or [],
            advice_text=result.advice_text,
            created_at=result.created_at,
        )

    @staticmethod
    def _build_daily_summaries(meals: list[MealLog]) -> list[FoodDailyMealSummaryResponse]:
        grouped: dict[date, list[MealLog]] = {}
        for meal in meals:
            grouped.setdefault(meal.meal_date, []).append(meal)

        return [
            FoodDailyMealSummaryResponse(
                meal_date=meal_date,
                nutrition_summary=FoodAnalysisService._build_meal_summary(day_meals),
            )
            for meal_date, day_meals in sorted(grouped.items(), reverse=True)
        ]

    @staticmethod
    def _build_meal_summary(meals: list[MealLog]) -> MealNutritionSummaryResponse:
        return MealNutritionSummaryResponse(
            meal_count=len(meals),
            total_calories=sum(meal.calories or 0 for meal in meals),
            total_sodium_mg=round(sum(float(meal.sodium_mg or 0) for meal in meals), 2),
            total_sugar_g=round(sum(float(meal.sugar_g or 0) for meal in meals), 2),
            total_fiber_g=round(sum(float(meal.fiber_g or 0) for meal in meals), 2),
            total_protein_g=round(sum(float(meal.protein_g or 0) for meal in meals), 2),
        )

    @staticmethod
    def _optional_decimal(value: int | float | None) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        return float(value) if value is not None else None

    @staticmethod
    def _limit_text(text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _today() -> date:
        return datetime.now(config.TIMEZONE).date()
