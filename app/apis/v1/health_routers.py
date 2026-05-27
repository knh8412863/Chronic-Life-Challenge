from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.predictions import (
    DataResponse,
    HealthSurveyCreateRequest,
    HealthSurveyCreateResponse,
    LipidObesityRecordCreateRequest,
    OptionalRecordCreateResponse,
    RenalRecordCreateRequest,
)
from app.models.users import User
from app.services.predictions import HealthInputService

health_router = APIRouter(tags=["health"])


@health_router.post(
    "/prediction-inputs",
    response_model=DataResponse[HealthSurveyCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_prediction_input(
    request: HealthSurveyCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_survey(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@health_router.post(
    "/health/lipid-obesity-records",
    response_model=DataResponse[OptionalRecordCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_lipid_obesity_record(
    request: LipidObesityRecordCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_lipid_obesity_record(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@health_router.post(
    "/health/renal-records",
    response_model=DataResponse[OptionalRecordCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_renal_record(
    request: RenalRecordCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_renal_record(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)
