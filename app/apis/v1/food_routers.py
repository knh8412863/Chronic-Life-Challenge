from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.foods import FoodAnalysisRequest, FoodAnalysisResponse
from app.dtos.predictions import DataResponse
from app.models.users import User
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
