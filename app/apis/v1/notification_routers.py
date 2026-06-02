from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.notifications import (
    NotificationMarkAllReadResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.notifications import NotificationService

notification_router = APIRouter(tags=["notifications"])


@notification_router.get(
    "/notifications",
    response_model=DataResponse[list[NotificationResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_notifications(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    unread_only: bool = False,
) -> Response:
    result = await service.get_notifications(user, limit, unread_only)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@notification_router.get(
    "/notifications/unread-count",
    response_model=DataResponse[NotificationUnreadCountResponse],
    status_code=status.HTTP_200_OK,
)
async def get_unread_notification_count(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    result = await service.get_unread_count(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@notification_router.patch(
    "/notifications/{notification_id}/read",
    response_model=DataResponse[NotificationMarkReadResponse],
    status_code=status.HTTP_200_OK,
)
async def mark_notification_read(
    notification_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    result = await service.mark_read(user, notification_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@notification_router.patch(
    "/notifications/read-all",
    response_model=DataResponse[NotificationMarkAllReadResponse],
    status_code=status.HTTP_200_OK,
)
async def mark_all_notifications_read(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    result = await service.mark_all_read(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
