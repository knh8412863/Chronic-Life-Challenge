from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.advices import (
    AdviceFeedbackCreateRequest,
    AdviceFeedbackCreateResponse,
    AdviceGenerateRequest,
    DailyAdviceResponse,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.advices import AdviceService

advice_router = APIRouter(tags=["advices"])


@advice_router.get(
    "/daily-advices/today",
    response_model=DataResponse[DailyAdviceResponse],
    status_code=status.HTTP_200_OK,
)
async def get_today_advice(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[AdviceService, Depends(AdviceService)],
) -> Response:
    result = await service.get_today(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@advice_router.post(
    "/daily-advices/generate",
    response_model=DataResponse[DailyAdviceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_today_advice(
    request: AdviceGenerateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[AdviceService, Depends(AdviceService)],
) -> Response:
    result = await service.generate_today(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@advice_router.post(
    "/daily-advices/{advice_id}/feedbacks",
    response_model=DataResponse[AdviceFeedbackCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_advice_feedback(
    advice_id: int,
    request: AdviceFeedbackCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[AdviceService, Depends(AdviceService)],
) -> Response:
    result = await service.create_feedback(user, advice_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)
