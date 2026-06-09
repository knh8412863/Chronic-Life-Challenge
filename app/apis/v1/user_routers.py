from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from starlette.responses import Response as EmptyResponse

from app.dependencies.security import get_request_user
from app.dtos.users import (
    ConsentUpdateRequest,
    PasswordChangeRequest,
    PolicyDocumentResponse,
    UserConsentItemResponse,
    UserConsentListResponse,
    UserInfoResponse,
    UserUpdateRequest,
    UserWithdrawalRequest,
)
from app.models.users import ConsentType, User
from app.services.users import UserManageService

user_router = APIRouter(prefix="/users", tags=["users"])
policy_router = APIRouter(prefix="/policy-documents", tags=["users"])


@user_router.get("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def user_me_info(
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    result = await user_manage_service.get_user_info(user)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@user_router.patch("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def update_user_me_info(
    update_data: UserUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    result = await user_manage_service.update_user_info(user=user, data=update_data)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@user_router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_me_password(
    request: PasswordChangeRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> EmptyResponse:
    await user_manage_service.change_password(user=user, data=request)
    return EmptyResponse(status_code=status.HTTP_204_NO_CONTENT)


@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_user_me(
    request: UserWithdrawalRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> EmptyResponse:
    await user_manage_service.withdraw_user(user=user, data=request)
    return EmptyResponse(status_code=status.HTTP_204_NO_CONTENT)


@user_router.get(
    "/me/consents",
    response_model=UserConsentListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_consents(
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    result = await user_manage_service.get_consents(user)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@user_router.patch(
    "/me/consents/{consent_type}",
    response_model=UserConsentItemResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user_consent(
    consent_type: ConsentType,
    request: ConsentUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    result = await user_manage_service.update_consent(user, consent_type, request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@policy_router.get(
    "/{policy_type}",
    response_model=PolicyDocumentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_policy_document(
    policy_type: ConsentType,
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
    version: str | None = None,
) -> Response:
    result = await user_manage_service.get_policy_document(policy_type, version)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
