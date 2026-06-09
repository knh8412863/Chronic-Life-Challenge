from datetime import date

import pytest
from fastapi import HTTPException

from app.apis.v1.health_routers import ensure_valid_date_range


def test_health_query_date_range_allows_open_ended_range():
    ensure_valid_date_range(None, date(2026, 6, 9))
    ensure_valid_date_range(date(2026, 6, 1), None)


def test_health_query_date_range_rejects_start_after_end():
    with pytest.raises(HTTPException) as exc_info:
        ensure_valid_date_range(date(2026, 6, 10), date(2026, 6, 1))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "조회 시작일은 종료일보다 늦을 수 없습니다."
