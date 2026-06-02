from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.predictions import (
    DataResponse,
    HealthSurveyCreateRequest,
    HealthSurveyCreateResponse,
    HealthSurveyRecordResponse,
    LipidObesityRecordCreateRequest,
    LipidObesityRecordResponse,
    MetricAssessmentResponse,
    OptionalRecordCreateResponse,
    RenalRecordCreateRequest,
    RenalRecordResponse,
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


@health_router.get(
    "/prediction-inputs",
    response_model=DataResponse[list[HealthSurveyRecordResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_prediction_inputs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Response:
    result = await service.get_health_surveys(user, limit)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/prediction-inputs/latest",
    response_model=DataResponse[HealthSurveyRecordResponse],
    status_code=status.HTTP_200_OK,
)
async def get_latest_prediction_input(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_latest_health_survey(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


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


@health_router.get(
    "/health/lipid-obesity-records",
    response_model=DataResponse[list[LipidObesityRecordResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_lipid_obesity_records(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Response:
    result = await service.get_lipid_obesity_records(user, limit)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/lipid-obesity-records/{record_id}",
    response_model=DataResponse[LipidObesityRecordResponse],
    status_code=status.HTTP_200_OK,
)
async def get_lipid_obesity_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_lipid_obesity_record(user, record_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


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


@health_router.get(
    "/health/renal-records",
    response_model=DataResponse[list[RenalRecordResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_renal_records(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Response:
    result = await service.get_renal_records(user, limit)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/renal-records/{record_id}",
    response_model=DataResponse[RenalRecordResponse],
    status_code=status.HTTP_200_OK,
)
async def get_renal_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_renal_record(user, record_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/metric-assessments",
    response_model=DataResponse[MetricAssessmentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_metric_assessments(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_metric_assessments(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
