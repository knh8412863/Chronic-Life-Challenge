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
            "vital_record_count": 1,
            "activity_log_count": 1,
            "exercise_log_count": 1,
            "meal_log_count": 2,
            "prediction_count": 1,
            "at_risk_prediction_count": 0,
            "challenge_checkin_count": 3,
        },
        status="AVAILABLE",
        summary_cards=WeeklyReportService._build_summary_cards(
            {
                "health_survey_count": 1,
                "lipid_obesity_record_count": 0,
                "renal_record_count": 0,
                "vital_record_count": 1,
                "activity_log_count": 1,
                "exercise_log_count": 1,
                "meal_log_count": 2,
                "prediction_count": 1,
                "at_risk_prediction_count": 0,
                "challenge_checkin_count": 3,
            }
        ),
        metric_summaries=WeeklyReportService._build_metric_summaries(
            {
                "health_survey_count": 1,
                "lipid_obesity_record_count": 0,
                "renal_record_count": 0,
                "vital_record_count": 1,
                "activity_log_count": 1,
                "exercise_log_count": 1,
                "meal_log_count": 2,
                "prediction_count": 1,
                "at_risk_prediction_count": 0,
                "challenge_checkin_count": 3,
            }
        ),
        trend_summary=WeeklyReportService._build_trend_summary(None),
        challenge_summary=WeeklyReportService._build_challenge_summary(
            {
                "challenge_checkin_count": 3,
            }
        ),
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
    assert response.status == "AVAILABLE"
    assert response.summary_cards[0].label == "건강 기록"
    assert response.trend_summary.status == "UNAVAILABLE"
    assert response.challenge_summary.checkin_count == 3


def test_weekly_report_summary_cards_mark_risk_and_missing_records():
    source_summary = {
        "health_survey_count": 0,
        "lipid_obesity_record_count": 0,
        "renal_record_count": 0,
        "vital_record_count": 0,
        "meal_log_count": 0,
        "exercise_log_count": 0,
        "at_risk_prediction_count": 2,
        "challenge_checkin_count": 1,
    }

    cards = WeeklyReportService._build_summary_cards(source_summary)

    assert cards[0]["status"] == "UNAVAILABLE"
    assert cards[1]["value"] == "2건"
    assert cards[1]["status"] == "HIGH"
    assert cards[4]["status"] == "CAUTION"


def test_weekly_report_challenge_summary_calculates_completion_rate():
    summary = WeeklyReportService._build_challenge_summary({"challenge_checkin_count": 4})

    assert summary["checkin_count"] == 4
    assert summary["completion_rate"] == 57.1
    assert summary["status"] == "IN_PROGRESS"


def test_weekly_report_source_data_detection():
    empty = {
        "health_survey_count": 0,
        "lipid_obesity_record_count": 0,
        "renal_record_count": 0,
        "vital_record_count": 0,
        "activity_log_count": 0,
        "exercise_log_count": 0,
        "meal_log_count": 0,
        "prediction_count": 0,
        "challenge_checkin_count": 0,
    }
    available = {**empty, "meal_log_count": 1}

    assert WeeklyReportService._has_report_source_data(empty) is False
    assert WeeklyReportService._has_report_source_data(available) is True


def test_weekly_report_list_item_is_lightweight_summary():
    report = SimpleNamespace(
        id=9,
        week_start_date=date(2026, 6, 1),
        week_end_date=date(2026, 6, 7),
        report_text="이번 주 건강 기록은 총 4건 입력되었습니다. AI 예측 중 위험 신호가 포함된 결과가 1건 있습니다.",
        summary_cards=[
            {"label": "건강 기록", "value": "4건", "status": "NORMAL", "description": "기록 수"},
            {"label": "AI 위험 신호", "value": "1건", "status": "HIGH", "description": "위험 신호"},
        ],
        created_at=datetime(2026, 6, 2, 17, 0),
    )

    response = WeeklyReportService._to_list_item(report)

    assert response.report_id == 9
    assert response.overall_status == "HIGH"
    assert response.summary_text.startswith("이번 주 건강 기록")
    assert not hasattr(response, "source_summary")


def test_weekly_report_summary_text_is_trimmed():
    text = "가" * 100

    result = WeeklyReportService._summary_text(text, max_length=10)

    assert len(result) == 10
    assert result.endswith("…")


def test_weekly_report_overall_status_priority():
    assert WeeklyReportService._overall_status([{"status": "NORMAL"}, {"status": "CAUTION"}]) == "CAUTION"
    assert WeeklyReportService._overall_status([{"status": "HIGH"}, {"status": "CAUTION"}]) == "HIGH"
    assert WeeklyReportService._overall_status([]) == "UNAVAILABLE"
