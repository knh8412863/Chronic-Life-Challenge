from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.dashboard import (
    DashboardChallengeCalendarResponse,
    DashboardKoreaComparisonResponse,
    DashboardRiskTrendResponse,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.dashboard import DashboardService

dashboard_router = APIRouter(tags=["dashboard"])


@dashboard_router.get(
    "/dashboard/risk-trends",
    response_model=DataResponse[DashboardRiskTrendResponse],
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_risk_trends(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DashboardService, Depends(DashboardService)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Response:
    result = await service.get_risk_trends(user, limit=limit)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@dashboard_router.get(
    "/dashboard/challenge-calendars",
    response_model=DataResponse[DashboardChallengeCalendarResponse],
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_challenge_calendars(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DashboardService, Depends(DashboardService)],
    from_date: date | None = None,
    to_date: date | None = None,
) -> Response:
    result = await service.get_challenge_calendars(user, from_date=from_date, to_date=to_date)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@dashboard_router.get(
    "/dashboard/korea-comparisons",
    response_model=DataResponse[DashboardKoreaComparisonResponse],
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_korea_comparisons(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DashboardService, Depends(DashboardService)],
) -> Response:
    result = await service.get_korea_comparisons(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
