from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.predictions import DataResponse
from app.dtos.reports import (
    CurrentWeeklyReportResponse,
    WeeklyReportExportResponse,
    WeeklyReportGenerateRequest,
    WeeklyReportListItemResponse,
    WeeklyReportResponse,
)
from app.models.users import User
from app.services.reports import WeeklyReportService

report_router = APIRouter(tags=["reports"])


@report_router.post(
    "/weekly-reports/generate",
    response_model=DataResponse[WeeklyReportResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_weekly_report(
    request: WeeklyReportGenerateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[WeeklyReportService, Depends(WeeklyReportService)],
) -> Response:
    result = await service.generate_current_week(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@report_router.get(
    "/weekly-reports/current",
    response_model=DataResponse[CurrentWeeklyReportResponse],
    status_code=status.HTTP_200_OK,
)
async def get_current_weekly_report(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[WeeklyReportService, Depends(WeeklyReportService)],
) -> Response:
    result = await service.get_current_week(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@report_router.get(
    "/weekly-reports",
    response_model=DataResponse[list[WeeklyReportListItemResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_weekly_reports(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[WeeklyReportService, Depends(WeeklyReportService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Response:
    result = await service.get_reports(user, limit)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@report_router.get(
    "/weekly-reports/{report_id}",
    response_model=DataResponse[WeeklyReportResponse],
    status_code=status.HTTP_200_OK,
)
async def get_weekly_report(
    report_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[WeeklyReportService, Depends(WeeklyReportService)],
) -> Response:
    result = await service.get_report(user, report_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@report_router.get(
    "/weekly-reports/{report_id}/exports",
    response_model=DataResponse[WeeklyReportExportResponse],
    status_code=status.HTTP_200_OK,
)
async def export_weekly_report(
    report_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[WeeklyReportService, Depends(WeeklyReportService)],
    export_format: Annotated[str, Query(pattern="^(JSON|CSV|PDF)$")] = "JSON",
    send_email: bool = False,
) -> Response:
    result = await service.export_report(user, report_id, export_format, send_email=send_email)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
