import os
import uuid
import zoneinfo
from dataclasses import field
from enum import StrEnum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    ENV: Env = Env.LOCAL
    SECRET_KEY: str = f"default-secret-key{uuid.uuid4().hex}"
    TIMEZONE: zoneinfo.ZoneInfo = field(default_factory=lambda: zoneinfo.ZoneInfo("Asia/Seoul"))
    TEMPLATE_DIR: str = os.path.join(Path(__file__).resolve().parent.parent, "templates")

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_EXPOSE_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "pw1234"
    DB_ROOT_PASSWORD: str = "pw1234"
    DB_NAME: str = "ai_health"
    DB_CONNECT_TIMEOUT: int = 5
    DB_CONNECTION_POOL_MAXSIZE: int = 10
    TEST_DB_HOST: str | None = None
    TEST_DB_PORT: int | None = None
    TEST_DB_USER: str | None = None
    TEST_DB_PASSWORD: str | None = None
    TEST_DB_NAME: str = "test"

    REDIS_URL: str | None = None

    COOKIE_DOMAIN: str = "localhost"
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    CORS_ALLOW_CREDENTIALS: bool = True

    SECURITY_CSP: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://accounts.google.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://lh3.googleusercontent.com; "
        "connect-src 'self' https://accounts.google.com https://www.googleapis.com; "
        "frame-src https://accounts.google.com; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    )
    HSTS_MAX_AGE_SECONDS: int = 31_536_000

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60
    JWT_LEEWAY: int = 5

    AUTH_RATE_LIMIT_MAX_FAILURES: int = 3
    AUTH_RATE_LIMIT_MAX_IP_FAILURES: int = 30
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60

    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    EMAIL_VERIFICATION_COOLDOWN_SECONDS: int = 60
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_COOLDOWN_SECONDS: int = 60

    FRONTEND_BASE_URL: str = "http://localhost:5173"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "no-reply@all4health.local"
    SMTP_USE_TLS: bool = True

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_JWKS_URL: str = "https://www.googleapis.com/oauth2/v3/certs"
    GOOGLE_ISSUERS: str = "https://accounts.google.com,accounts.google.com"

    ADVICE_LLM_ENABLED: bool = False
    REPORT_LLM_ENABLED: bool = False
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT_SECONDS: float = 10.0

    def get_cors_allow_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]
