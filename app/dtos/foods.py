from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.dtos.predictions import MealType


class FoodAnalysisRequest(BaseModel):
    meal_date: date | None = None
    meal_type: MealType | None = None
    food_name: Annotated[str, Field(min_length=1, max_length=100)]
    amount: Annotated[str | None, Field(default=None, max_length=50)]
    calories: Annotated[int | None, Field(default=None, ge=0, le=10000)]
    carbs_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    protein_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    fat_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    sodium_mg: Annotated[float | None, Field(default=None, ge=0, le=100000)]
    sugar_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    fiber_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]


class FoodNutritionResponse(BaseModel):
    calories: int | None = None
    carbs_g: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    fiber_g: float | None = None


class FoodAnalysisResponse(BaseModel):
    food_analysis_result_id: int
    task_uuid: str
    status: Literal["SUCCESS", "FAILED"]
    meal_date: date | None = None
    meal_type: MealType | None = None
    food_name: str
    amount: str | None = None
    nutrition: FoodNutritionResponse
    health_score: int
    risk_flags: list[str]
    advice_text: str
    created_at: datetime


class MealNutritionSummaryResponse(BaseModel):
    meal_count: int
    total_calories: int
    total_sodium_mg: float
    total_sugar_g: float
    total_fiber_g: float
    total_protein_g: float


class LatestFoodAnalysisAdviceResponse(BaseModel):
    food_analysis_result_id: int
    task_uuid: str
    food_name: str
    health_score: int
    risk_flags: list[str]
    advice_text: str
    created_at: datetime


class FoodTodayMealSummaryResponse(BaseModel):
    summary_date: date
    nutrition_summary: MealNutritionSummaryResponse
    latest_analysis_advice: LatestFoodAnalysisAdviceResponse | None = None


class FoodDailyMealSummaryResponse(BaseModel):
    meal_date: date
    nutrition_summary: MealNutritionSummaryResponse


class FoodPeriodMealSummaryResponse(BaseModel):
    period_start: date
    period_end: date
    daily_summaries: list[FoodDailyMealSummaryResponse]
