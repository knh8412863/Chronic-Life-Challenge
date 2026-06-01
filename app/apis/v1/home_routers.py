from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.home import HomeSummaryResponse
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.home import HomeService

home_router = APIRouter(tags=["home"])


@home_router.get(
    "/home/summary",
    response_model=DataResponse[HomeSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_home_summary(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HomeService, Depends(HomeService)],
) -> Response:
    result = await service.get_summary(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
