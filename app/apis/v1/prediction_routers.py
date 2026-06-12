from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.predictions import (
    DataResponse,
    PredictionFeedbackCreateRequest,
    PredictionFeedbackCreateResponse,
    PredictionResultListResponse,
    PredictionResultResponse,
    PredictionTaskCreateRequest,
    PredictionTaskCreateResponse,
    PredictionTaskStatusResponse,
)
from app.models.users import User
from app.services.predictions import PredictionService

prediction_router = APIRouter(tags=["predictions"])


@prediction_router.post(
    "/prediction-tasks",
    response_model=DataResponse[PredictionTaskCreateResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_prediction_task(
    request: PredictionTaskCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PredictionService, Depends(PredictionService)],
) -> Response:
    task = await service.create_task(user, request)
    return Response({"data": task.model_dump(mode="json")}, status_code=status.HTTP_202_ACCEPTED)


@prediction_router.get(
    "/prediction-tasks/{task_uuid}/status",
    response_model=DataResponse[PredictionTaskStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def get_prediction_task_status(
    task_uuid: str,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PredictionService, Depends(PredictionService)],
) -> Response:
    task = await service.get_task_status(user, task_uuid)
    return Response({"data": task.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@prediction_router.get(
    "/prediction-results",
    response_model=DataResponse[PredictionResultListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_prediction_results(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PredictionService, Depends(PredictionService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Response:
    results = await service.get_results(user, limit)
    return Response({"data": results.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@prediction_router.get(
    "/prediction-results/{result_id}",
    response_model=DataResponse[PredictionResultResponse],
    status_code=status.HTTP_200_OK,
)
async def get_prediction_result(
    result_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PredictionService, Depends(PredictionService)],
) -> Response:
    result = await service.get_result(user, result_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@prediction_router.post(
    "/prediction-results/{result_id}/feedbacks",
    response_model=DataResponse[PredictionFeedbackCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_prediction_feedback(
    result_id: int,
    request: PredictionFeedbackCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PredictionService, Depends(PredictionService)],
) -> Response:
    result = await service.create_feedback(user, result_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)
