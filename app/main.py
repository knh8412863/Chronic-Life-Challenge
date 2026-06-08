from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.apis.v1 import v1_routers
from app.core import config
from app.core.db.databases import initialize_tortoise
from app.core.exceptions import register_exception_handlers
from app.core.middlewares import add_security_headers

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_cors_allow_origins(),
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
app.middleware("http")(add_security_headers)
register_exception_handlers(app)

initialize_tortoise(app)

app.include_router(v1_routers)
