import asyncio
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from tortoise import generate_config
from tortoise.contrib.test import finalizer, initializer

from app.core import config
from app.core.db.databases import TORTOISE_APP_MODELS

TEST_BASE_URL = "http://test"
TEST_DB_LABEL = "models"
TEST_DB_TZ = "Asia/Seoul"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_dotenv() -> dict[str, str]:
    env_path = PROJECT_ROOT / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def test_env_value(key: str, dotenv_values: dict[str, str], default: str) -> str:
    return os.getenv(f"TEST_{key}") or dotenv_values.get(f"TEST_{key}") or dotenv_values.get(key) or default


def get_test_db_config() -> dict[str, Any]:
    dotenv_values = read_dotenv()
    test_host = test_env_value("DB_HOST", dotenv_values, "127.0.0.1")
    if test_host in {"localhost", "mysql"}:
        test_host = "127.0.0.1"
    test_port = (
        os.getenv("TEST_DB_PORT") or dotenv_values.get("TEST_DB_PORT") or dotenv_values.get("DB_EXPOSE_PORT", "3306")
    )
    test_user = os.getenv("TEST_DB_USER") or dotenv_values.get("TEST_DB_USER") or "root"
    test_password = (
        os.getenv("TEST_DB_PASSWORD")
        or dotenv_values.get("TEST_DB_PASSWORD")
        or dotenv_values.get("DB_ROOT_PASSWORD")
        or config.DB_ROOT_PASSWORD
    )
    test_db_name = os.getenv("TEST_DB_NAME") or dotenv_values.get("TEST_DB_NAME") or config.TEST_DB_NAME
    tortoise_config = generate_config(
        db_url=f"mysql://{test_user}:{test_password}@{test_host}:{test_port}/{test_db_name}",
        app_modules={TEST_DB_LABEL: TORTOISE_APP_MODELS},
        connection_label=TEST_DB_LABEL,
        testing=True,
    )
    tortoise_config["timezone"] = TEST_DB_TZ

    return tortoise_config


def requires_db(request: FixtureRequest) -> bool:
    return any("app/tests/unit/" not in item.nodeid for item in request.session.items)


@pytest.fixture(scope="session", autouse=True)
def initialize(request: FixtureRequest) -> Generator[None, None]:
    if not requires_db(request):
        yield
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with patch("tortoise.contrib.test.getDBConfig", Mock(return_value=get_test_db_config())):
        initializer(modules=TORTOISE_APP_MODELS)
    yield
    finalizer()
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")  # type: ignore[type-var]
def event_loop() -> None:
    pass
