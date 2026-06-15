from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.foods import (
    FoodAnalysisRequest,
    FoodAnalysisResponse,
    FoodNutritionOcrResponse,
    FoodPeriodMealSummaryResponse,
    FoodTodayMealSummaryResponse,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.clova_ocr import ClovaOcrService
from app.services.foods import FoodAnalysisService

food_router = APIRouter(tags=["foods"])


@food_router.post(
    "/food/analyze",
    response_model=DataResponse[FoodAnalysisResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_food_analysis(
    request: FoodAnalysisRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[FoodAnalysisService, Depends(FoodAnalysisService)],
) -> Response:
    result = await service.analyze(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@food_router.get(
    "/food/analyze/{task_uuid}",
    response_model=DataResponse[FoodAnalysisResponse],
    status_code=status.HTTP_200_OK,
)
async def get_food_analysis(
    task_uuid: str,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[FoodAnalysisService, Depends(FoodAnalysisService)],
) -> Response:
    result = await service.get_result(user, task_uuid)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@food_router.post(
    "/food/nutrition-ocr",
    response_model=DataResponse[FoodNutritionOcrResponse],
    status_code=status.HTTP_200_OK,
)
async def analyze_food_nutrition_label_file(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ClovaOcrService, Depends(ClovaOcrService)],
    file: Annotated[UploadFile, File(...)],
) -> Response:
    content = await file.read()
    result = await service.analyze_food_nutrition_label_file(
        file_name=file.filename or "nutrition-label",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@food_router.get(
    "/food/meals/summary/today",
    response_model=DataResponse[FoodTodayMealSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_today_meal_summary(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[FoodAnalysisService, Depends(FoodAnalysisService)],
) -> Response:
    result = await service.get_today_meal_summary(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@food_router.get(
    "/food/meals/summary",
    response_model=DataResponse[FoodPeriodMealSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_period_meal_summary(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[FoodAnalysisService, Depends(FoodAnalysisService)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> Response:
    result = await service.get_period_meal_summary(user, from_date, to_date)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
