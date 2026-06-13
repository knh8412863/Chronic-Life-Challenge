from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import default_logger

ERROR_CODE_BY_STATUS = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_410_GONE: "GONE",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "VALIDATION_ERROR",
    status.HTTP_423_LOCKED: "LOCKED",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
}


def build_error_response(
    *,
    status_code: int,
    detail: Any,
    code: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    if message is None:
        message = detail if isinstance(detail, str) else "요청을 처리할 수 없습니다."

    return {
        "detail": detail,
        "error": {
            "code": code or ERROR_CODE_BY_STATUS.get(status_code, "HTTP_ERROR"),
            "message": message,
            "status_code": status_code,
        },
    }


def _make_json_serializable(value: Any) -> Any:
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, list):
        return [_make_json_serializable(item) for item in value]
    if isinstance(value, tuple):
        return [_make_json_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: _make_json_serializable(item) for key, item in value.items()}
    return value


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content=build_error_response(status_code=exc.status_code, detail=exc.detail),
        headers=exc.headers,
    )


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_make_json_serializable(exc.errors()),
            code="VALIDATION_ERROR",
            message="입력값 형식이 올바르지 않습니다.",
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    default_logger.exception("Unhandled server error")
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 오류가 발생했습니다.",
            code="INTERNAL_SERVER_ERROR",
            message="서버 오류가 발생했습니다.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
