from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response
from starlette.responses import Response as EmptyResponse

from app.dependencies.security import get_request_user
from app.dtos.predictions import (
    ActivityLogCreateRequest,
    ActivityLogListResponse,
    ActivityLogResponse,
    ActivityLogUpdateRequest,
    DataResponse,
    ExerciseLogCreateRequest,
    ExerciseLogListResponse,
    ExerciseLogResponse,
    ExerciseLogUpdateRequest,
    ExerciseType,
    HealthGoalResponse,
    HealthGoalUpdateRequest,
    HealthStatisticsResponse,
    HealthSurveyCreateRequest,
    HealthSurveyCreateResponse,
    HealthSurveyRecordResponse,
    LipidObesityRecordCreateRequest,
    LipidObesityRecordResponse,
    MealLogCreateRequest,
    MealLogCreateResponse,
    MealLogListResponse,
    MealLogResponse,
    MealLogUpdateRequest,
    MealType,
    MetricAssessmentResponse,
    OptionalRecordCreateResponse,
    RenalRecordCreateRequest,
    RenalRecordResponse,
    VitalMeasureType,
    VitalRecordCreateRequest,
    VitalRecordDetailResponse,
    VitalRecordListResponse,
    VitalRecordResponse,
    VitalRecordUpdateRequest,
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


@health_router.post(
    "/health/vitals",
    response_model=DataResponse[OptionalRecordCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_vital_record(
    request: VitalRecordCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_vital_record(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@health_router.get(
    "/health/vitals",
    response_model=DataResponse[VitalRecordListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_vital_records(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    measure_type: VitalMeasureType | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Response:
    result = await service.get_vital_records(user, from_date, to_date, measure_type, limit)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/vitals/{record_id}",
    response_model=DataResponse[VitalRecordDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_vital_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_vital_record(user, record_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.patch(
    "/health/vitals/{record_id}",
    response_model=DataResponse[VitalRecordResponse],
    status_code=status.HTTP_200_OK,
)
async def update_vital_record(
    record_id: int,
    request: VitalRecordUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.update_vital_record(user, record_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.delete(
    "/health/vitals/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_vital_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> EmptyResponse:
    await service.delete_vital_record(user, record_id)
    return EmptyResponse(status_code=status.HTTP_204_NO_CONTENT)


@health_router.post(
    "/health/activity-logs",
    response_model=DataResponse[OptionalRecordCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_activity_log(
    request: ActivityLogCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_activity_log(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@health_router.get(
    "/health/activity-logs",
    response_model=DataResponse[ActivityLogListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_activity_logs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Response:
    result = await service.get_activity_logs(user, from_date, to_date, limit)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/activity-logs/{activity_log_id}",
    response_model=DataResponse[ActivityLogResponse],
    status_code=status.HTTP_200_OK,
)
async def get_activity_log(
    activity_log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_activity_log(user, activity_log_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.patch(
    "/health/activity-logs/{activity_log_id}",
    response_model=DataResponse[ActivityLogResponse],
    status_code=status.HTTP_200_OK,
)
async def update_activity_log(
    activity_log_id: int,
    request: ActivityLogUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.update_activity_log(user, activity_log_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.delete(
    "/health/activity-logs/{activity_log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_activity_log(
    activity_log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> EmptyResponse:
    await service.delete_activity_log(user, activity_log_id)
    return EmptyResponse(status_code=status.HTTP_204_NO_CONTENT)


@health_router.get(
    "/health/goals",
    response_model=DataResponse[HealthGoalResponse],
    status_code=status.HTTP_200_OK,
)
async def get_health_goal(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_health_goal(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.patch(
    "/health/goals",
    response_model=DataResponse[HealthGoalResponse],
    status_code=status.HTTP_200_OK,
)
async def update_health_goal(
    request: HealthGoalUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.update_health_goal(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.post(
    "/health/exercise-logs",
    response_model=DataResponse[OptionalRecordCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_exercise_log(
    request: ExerciseLogCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_exercise_log(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@health_router.get(
    "/health/exercise-logs",
    response_model=DataResponse[ExerciseLogListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_exercise_logs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    exercise_type: ExerciseType | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Response:
    result = await service.get_exercise_logs(user, from_date, to_date, exercise_type, limit)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/exercise-logs/{exercise_log_id}",
    response_model=DataResponse[ExerciseLogResponse],
    status_code=status.HTTP_200_OK,
)
async def get_exercise_log(
    exercise_log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_exercise_log(user, exercise_log_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.patch(
    "/health/exercise-logs/{exercise_log_id}",
    response_model=DataResponse[ExerciseLogResponse],
    status_code=status.HTTP_200_OK,
)
async def update_exercise_log(
    exercise_log_id: int,
    request: ExerciseLogUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.update_exercise_log(user, exercise_log_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.delete(
    "/health/exercise-logs/{exercise_log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_exercise_log(
    exercise_log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> EmptyResponse:
    await service.delete_exercise_log(user, exercise_log_id)
    return EmptyResponse(status_code=status.HTTP_204_NO_CONTENT)


@health_router.post(
    "/health/meals",
    response_model=DataResponse[MealLogCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_meal_log(
    request: MealLogCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.create_meal_log(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@health_router.get(
    "/health/meals",
    response_model=DataResponse[MealLogListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_meal_logs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    meal_type: MealType | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Response:
    result = await service.get_meal_logs(user, from_date, to_date, meal_type, limit)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.get(
    "/health/meals/{meal_log_id}",
    response_model=DataResponse[MealLogResponse],
    status_code=status.HTTP_200_OK,
)
async def get_meal_log(
    meal_log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.get_meal_log(user, meal_log_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.patch(
    "/health/meals/{meal_log_id}",
    response_model=DataResponse[MealLogResponse],
    status_code=status.HTTP_200_OK,
)
async def update_meal_log(
    meal_log_id: int,
    request: MealLogUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> Response:
    result = await service.update_meal_log(user, meal_log_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@health_router.delete(
    "/health/meals/{meal_log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meal_log(
    meal_log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
) -> EmptyResponse:
    await service.delete_meal_log(user, meal_log_id)
    return EmptyResponse(status_code=status.HTTP_204_NO_CONTENT)


@health_router.get(
    "/health/statistics",
    response_model=DataResponse[HealthStatisticsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_health_statistics(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInputService, Depends(HealthInputService)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> Response:
    result = await service.get_health_statistics(user, from_date, to_date)
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
