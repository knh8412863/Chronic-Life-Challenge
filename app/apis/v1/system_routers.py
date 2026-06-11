from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dtos.system import LivenessResponse, ReadinessResponse
from app.services.system import SystemService

system_router = APIRouter(tags=["system"])


@system_router.get("/health", response_model=LivenessResponse, status_code=status.HTTP_200_OK)
async def liveness(service: Annotated[SystemService, Depends(SystemService)]) -> Response:
    result = await service.liveness()
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@system_router.get("/readiness", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness(service: Annotated[SystemService, Depends(SystemService)]) -> Response:
    result = await service.readiness()
    code = status.HTTP_200_OK if result.status == "ready" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(result.model_dump(mode="json"), status_code=code)
