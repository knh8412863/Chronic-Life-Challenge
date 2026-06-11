from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.challenges import (
    ChallengeBadgeListResponse,
    ChallengeCancelResponse,
    ChallengeCheckinCreateRequest,
    ChallengeCheckinResponse,
    ChallengeDashboardSummaryResponse,
    ChallengeDetailResponse,
    ChallengeJoinResponse,
    ChallengeSummaryResponse,
    ChallengeWeeklyLeaderboardResponse,
    MyChallengeResponse,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.challenges import ChallengeService

challenge_router = APIRouter(tags=["challenges"])


@challenge_router.get(
    "/challenges",
    response_model=DataResponse[list[ChallengeSummaryResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_challenges(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
    category: Annotated[str | None, Query(max_length=30)] = None,
    target_metric: Annotated[str | None, Query(max_length=30)] = None,
    sort: Annotated[str, Query(pattern="^(LATEST|POPULAR|DURATION)$")] = "LATEST",
) -> Response:
    result = await service.get_challenges(user, category=category, target_metric=target_metric, sort=sort)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@challenge_router.get(
    "/challenges/summary",
    response_model=DataResponse[ChallengeDashboardSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_challenge_summary(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.get_dashboard_summary(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@challenge_router.get(
    "/challenges/{challenge_id}",
    response_model=DataResponse[ChallengeDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_challenge(
    challenge_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.get_challenge(user, challenge_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@challenge_router.post(
    "/challenges/{challenge_id}/participations",
    response_model=DataResponse[ChallengeJoinResponse],
    status_code=status.HTTP_201_CREATED,
)
async def join_challenge(
    challenge_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.join_challenge(user, challenge_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@challenge_router.get(
    "/challenge-participations/me",
    response_model=DataResponse[list[MyChallengeResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_my_challenges(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.get_my_challenges(user)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)


@challenge_router.get(
    "/challenge-participations/{participation_id}",
    response_model=DataResponse[MyChallengeResponse],
    status_code=status.HTTP_200_OK,
)
async def get_challenge_participation(
    participation_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.get_participation(user, participation_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@challenge_router.post(
    "/challenge-participations/{participation_id}/checkins/today",
    response_model=DataResponse[ChallengeCheckinResponse],
    status_code=status.HTTP_201_CREATED,
)
async def checkin_today(
    participation_id: int,
    request: ChallengeCheckinCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.checkin_today(user, participation_id, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@challenge_router.post(
    "/challenge-participations/{participation_id}/cancellations",
    response_model=DataResponse[ChallengeCancelResponse],
    status_code=status.HTTP_200_OK,
)
async def cancel_challenge_participation(
    participation_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
) -> Response:
    result = await service.cancel_participation(user, participation_id)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@challenge_router.get(
    "/badges",
    response_model=DataResponse[ChallengeBadgeListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_badges(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
    badge_filter: Annotated[str, Query(pattern="^(ALL|STREAK_3|STREAK_7|STREAK_30)$")] = "ALL",
) -> Response:
    result = await service.get_badges(user, badge_filter=badge_filter)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@challenge_router.get(
    "/challenge-leaderboards/weekly",
    response_model=DataResponse[ChallengeWeeklyLeaderboardResponse],
    status_code=status.HTTP_200_OK,
)
async def get_weekly_challenge_leaderboard(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
    week_start: date | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Response:
    result = await service.get_weekly_leaderboard(user, week_start=week_start, limit=limit)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@challenge_router.get(
    "/challenge-recommendations",
    response_model=DataResponse[list[ChallengeSummaryResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_challenge_recommendations(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChallengeService, Depends(ChallengeService)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> Response:
    result = await service.get_recommendations(user, limit=limit)
    return Response({"data": [item.model_dump(mode="json") for item in result]}, status_code=status.HTTP_200_OK)
