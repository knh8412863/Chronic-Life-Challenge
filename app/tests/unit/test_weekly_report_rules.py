from datetime import date, datetime
from types import SimpleNamespace

from app.services.reports import RULE_BASED_MODEL, WeeklyReportService


def test_week_range_starts_on_monday_and_ends_on_sunday():
    week_start, week_end = WeeklyReportService._week_range(today=date(2026, 6, 2))

    assert week_start == date(2026, 6, 1)
    assert week_end == date(2026, 6, 7)


def test_rule_based_report_text_describes_missing_records():
    source_summary = {
        "health_survey_count": 0,
        "lipid_obesity_record_count": 0,
        "renal_record_count": 0,
        "prediction_count": 0,
        "at_risk_prediction_count": 0,
        "challenge_checkin_count": 0,
    }

    report_text = WeeklyReportService._build_report_text(source_summary)

    assert "건강 기록이 아직 없습니다" in report_text
    assert "AI 예측 결과가 없어" in report_text
    assert "챌린지 체크인이 없어" in report_text


def test_rule_based_report_text_describes_weekly_activity():
    source_summary = {
        "health_survey_count": 1,
        "lipid_obesity_record_count": 2,
        "renal_record_count": 1,
        "prediction_count": 2,
        "at_risk_prediction_count": 1,
        "challenge_checkin_count": 4,
    }

    report_text = WeeklyReportService._build_report_text(source_summary)

    assert "건강 기록은 총 4건" in report_text
    assert "위험 신호가 포함된 결과가 1건" in report_text
    assert "챌린지는 4회 체크인" in report_text


def test_weekly_report_response_marks_generated_state():
    report = SimpleNamespace(
        id=8,
        week_start_date=date(2026, 6, 1),
        week_end_date=date(2026, 6, 7),
        source_summary={
            "health_survey_count": 1,
            "lipid_obesity_record_count": 0,
            "renal_record_count": 0,
            "prediction_count": 1,
            "at_risk_prediction_count": 0,
            "challenge_checkin_count": 3,
        },
        report_text="이번 주 건강 기록은 총 1건 입력되었습니다.",
        provider="RULE_BASED",
        model_name=RULE_BASED_MODEL,
        created_at=datetime(2026, 6, 2, 17, 0),
    )

    response = WeeklyReportService._to_response(report, generated=True)

    assert response.report_id == 8
    assert response.generated is True
    assert response.source_summary.health_survey_count == 1
    assert response.model_name == RULE_BASED_MODEL
