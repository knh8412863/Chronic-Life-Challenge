from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core import config
from app.core.config import Env

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

DOCS_PATHS = {"/api/docs", "/api/redoc", "/api/openapi.json"}
DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'"
)


async def add_security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)

    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)

    csp = DOCS_CSP if request.url.path in DOCS_PATHS else config.SECURITY_CSP
    response.headers.setdefault("Content-Security-Policy", csp)

    if config.ENV == Env.PROD:
        response.headers.setdefault(
            "Strict-Transport-Security",
            f"max-age={config.HSTS_MAX_AGE_SECONDS}; includeSubDomains",
        )

    return response
