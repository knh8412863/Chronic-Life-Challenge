from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core import config
from app.core.config import Env
from app.dtos.auth import LoginRequest, LoginResponse, SignUpRequest, TokenRefreshResponse
from app.services.auth import AuthService
from app.services.jwt import JwtService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> JSONResponse:
    await auth_service.signup(request)
    return JSONResponse(
        content={"detail": "회원가입이 성공적으로 완료되었습니다."}, status_code=status.HTTP_201_CREATED
    )


@auth_router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> JSONResponse:
    client_ip = http_request.client.host if http_request.client else "unknown"
    user = await auth_service.authenticate(request, client_ip=client_ip)
    tokens = await auth_service.login(user)
    resp = JSONResponse(
        content=LoginResponse(access_token=str(tokens["access_token"])).model_dump(), status_code=status.HTTP_200_OK
    )
    cookie_options = {
        "key": "refresh_token",
        "value": str(tokens["refresh_token"]),
        "httponly": True,
        "secure": config.ENV == Env.PROD,
        "domain": config.COOKIE_DOMAIN or None,
        "samesite": "lax",
        "path": "/",
    }
    if request.remember_me:
        cookie_options["max_age"] = config.REFRESH_TOKEN_EXPIRE_MINUTES * 60

    resp.set_cookie(**cookie_options)
    return resp


@auth_router.delete("/sessions/current", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=config.ENV == Env.PROD,
        domain=config.COOKIE_DOMAIN or None,
        samesite="lax",
        path="/",
    )
    return resp


@auth_router.get("/token/refresh", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> JSONResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")
    access_token = jwt_service.refresh_jwt(refresh_token)
    return JSONResponse(
        content=TokenRefreshResponse(access_token=str(access_token)).model_dump(), status_code=status.HTTP_200_OK
    )
