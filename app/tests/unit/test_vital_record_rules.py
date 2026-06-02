from datetime import date, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.dtos.predictions import VitalMeasureType, VitalRecordCreateRequest
from app.services.predictions import HealthInputService


def test_vital_record_create_request_requires_bp_values_for_bp_type():
    request = VitalRecordCreateRequest(
        measured_at=datetime(2026, 6, 2, 8, 0),
        measure_type=VitalMeasureType.BP_MORNING,
        sbp=130,
        dbp=85,
        glucose=None,
    )

    assert request.sbp == 130
    assert request.dbp == 85


def test_vital_record_create_request_rejects_glucose_on_bp_type():
    with pytest.raises(ValidationError):
        VitalRecordCreateRequest(
            measured_at=datetime(2026, 6, 2, 8, 0),
            measure_type=VitalMeasureType.BP_MORNING,
            sbp=130,
            dbp=85,
            glucose=120,
        )


def test_vital_record_create_request_requires_glucose_for_glucose_type():
    request = VitalRecordCreateRequest(
        measured_at=datetime(2026, 6, 2, 8, 0),
        measure_type=VitalMeasureType.GLUCOSE_FASTING,
        glucose=105,
    )

    assert request.glucose == 105


def test_vital_critical_rule_detects_high_bp_and_glucose():
    assert HealthInputService._is_vital_critical("BP_MORNING", 180, 80, None) is True
    assert HealthInputService._is_vital_critical("BP_EVENING", 120, 110, None) is True
    assert HealthInputService._is_vital_critical("GLUCOSE_POSTPRANDIAL", None, None, 200) is True
    assert HealthInputService._is_vital_critical("GLUCOSE_FASTING", None, None, 110) is False


def test_vital_summary_averages_values_by_available_fields():
    records = [
        SimpleNamespace(sbp=120, dbp=80, glucose=None, is_critical=False),
        SimpleNamespace(sbp=140, dbp=90, glucose=None, is_critical=False),
        SimpleNamespace(sbp=None, dbp=None, glucose=210, is_critical=True),
    ]

    summary = HealthInputService._build_vital_summary(records)

    assert summary.avg_sbp == 130.0
    assert summary.avg_dbp == 85.0
    assert summary.avg_glucose == 210.0
    assert summary.critical_count == 1


def test_vital_record_response_maps_status_label():
    now = datetime(2026, 6, 2, 8, 0)
    record = SimpleNamespace(
        id=5,
        record_date=date(2026, 6, 2),
        measured_at=now,
        measure_type="GLUCOSE_FASTING",
        sbp=None,
        dbp=None,
        glucose=220,
        memo="공복",
        is_critical=True,
        created_at=now,
        updated_at=now,
    )

    result = HealthInputService._to_vital_record(record)

    assert result.record_id == 5
    assert result.measure_type == VitalMeasureType.GLUCOSE_FASTING
    assert result.status_label == "CRITICAL"
