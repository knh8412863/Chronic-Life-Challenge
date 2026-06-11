from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.predictions import DataResponse
from app.dtos.scores import HealthScoreHistoryResponse, HealthScoreResponse
from app.models.users import User
from app.services.scores import ScoreService

score_router = APIRouter(tags=["scores"])


@score_router.get("/scores/today", response_model=DataResponse[HealthScoreResponse], status_code=status.HTTP_200_OK)
async def get_today_score(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ScoreService, Depends(ScoreService)],
) -> Response:
    result = await service.get_today_score(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@score_router.get("/scores", response_model=DataResponse[HealthScoreHistoryResponse], status_code=status.HTTP_200_OK)
async def get_scores(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ScoreService, Depends(ScoreService)],
    from_date: date | None = None,
    to_date: date | None = None,
) -> Response:
    result = await service.get_scores(user, from_date=from_date, to_date=to_date)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
