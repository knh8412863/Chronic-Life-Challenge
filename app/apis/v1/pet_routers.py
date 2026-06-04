from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.pets import (
    VirtualPetCreateRequest,
    VirtualPetCreateResponse,
    VirtualPetNameUpdateRequest,
    VirtualPetNameUpdateResponse,
    VirtualPetStatusResponse,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.pets import VirtualPetService

pet_router = APIRouter(prefix="/virtual-pets", tags=["virtual-pets"])


@pet_router.get(
    "",
    response_model=DataResponse[VirtualPetStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_virtual_pet(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[VirtualPetService, Depends(VirtualPetService)],
) -> Response:
    result = await service.get_my_pet(user)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@pet_router.post(
    "",
    response_model=DataResponse[VirtualPetCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_virtual_pet(
    request: VirtualPetCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[VirtualPetService, Depends(VirtualPetService)],
) -> Response:
    result = await service.create_pet(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@pet_router.patch(
    "/me/name",
    response_model=DataResponse[VirtualPetNameUpdateResponse],
    status_code=status.HTTP_200_OK,
)
async def update_my_virtual_pet_name(
    request: VirtualPetNameUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[VirtualPetService, Depends(VirtualPetService)],
) -> Response:
    result = await service.update_pet_name(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)
