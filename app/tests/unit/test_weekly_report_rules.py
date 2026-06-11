from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.services.llm_advice import OPENAI_PROVIDER
from app.services.llm_report import OpenAIReportClient, ReportLLMError, ReportLLMResult
from app.services.reports import MAX_REPORT_TEXT_LENGTH, REPORT_DISCLAIMER, RULE_BASED_MODEL, WeeklyReportService


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
    assert response.source_type == "RULE_BASED"
    assert response.status == "AVAILABLE"
    assert response.summary_cards[0].label == "건강 기록"
    assert response.trend_summary.status == "UNAVAILABLE"
    assert response.challenge_summary.checkin_count == 3


def test_weekly_report_response_marks_openai_source_type():
    source_summary = {
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
    report = SimpleNamespace(
        id=18,
        week_start_date=date(2026, 6, 1),
        week_end_date=date(2026, 6, 7),
        source_summary=source_summary,
        status="AVAILABLE",
        summary_cards=WeeklyReportService._build_summary_cards(source_summary),
        metric_summaries=WeeklyReportService._build_metric_summaries(source_summary),
        trend_summary=WeeklyReportService._build_trend_summary(None),
        challenge_summary=WeeklyReportService._build_challenge_summary(source_summary),
        report_text="이번 주는 건강 기록과 챌린지 실천이 확인되었습니다.",
        provider=OPENAI_PROVIDER,
        model_name="gpt-4o-mini",
        created_at=datetime(2026, 6, 2, 17, 0),
    )

    response = WeeklyReportService._to_response(report, generated=True)

    assert response.source_type == "LLM"
    assert response.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_generate_llm_report_uses_openai_client_when_enabled(monkeypatch):
    class FakeOpenAIReportClient:
        is_configured = True

        def __init__(self, api_key: str | None, model_name: str, timeout_seconds: float) -> None:
            self.api_key = api_key
            self.model_name = model_name
            self.timeout_seconds = timeout_seconds

        async def generate(self, source_summary: dict[str, int], max_length: int) -> ReportLLMResult:
            return ReportLLMResult(
                report_text="이번 주에는 건강 기록과 챌린지 실천이 확인되었습니다. 다음 주에도 꾸준히 기록해 보세요.",
                provider=OPENAI_PROVIDER,
                model_name=self.model_name,
                input_tokens=30,
                output_tokens=45,
                cache_read_tokens=5,
            )

    monkeypatch.setattr("app.services.reports.config.REPORT_LLM_ENABLED", True)
    monkeypatch.setattr("app.services.reports.config.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.reports.config.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.reports.config.OPENAI_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("app.services.reports.OpenAIReportClient", FakeOpenAIReportClient)

    result = await WeeklyReportService._generate_llm_report({"meal_log_count": 2})

    assert result is not None
    assert result.provider == OPENAI_PROVIDER
    assert result.model_name == "gpt-4o-mini"
    assert result.input_tokens == 30
    assert "의료 진단" in result.report_text
    assert len(result.report_text) <= MAX_REPORT_TEXT_LENGTH


@pytest.mark.asyncio
async def test_generate_llm_report_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr("app.services.reports.config.REPORT_LLM_ENABLED", False)

    result = await WeeklyReportService._generate_llm_report({"meal_log_count": 2})

    assert result is None


@pytest.mark.asyncio
async def test_generate_llm_report_returns_none_when_client_fails(monkeypatch):
    class FailingOpenAIReportClient:
        is_configured = True

        def __init__(self, api_key: str | None, model_name: str, timeout_seconds: float) -> None:
            pass

        async def generate(self, source_summary: dict[str, int], max_length: int) -> ReportLLMResult:
            raise ReportLLMError("OpenAI weekly report generation failed.")

    monkeypatch.setattr("app.services.reports.config.REPORT_LLM_ENABLED", True)
    monkeypatch.setattr("app.services.reports.config.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.reports.config.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.reports.config.OPENAI_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("app.services.reports.OpenAIReportClient", FailingOpenAIReportClient)

    result = await WeeklyReportService._generate_llm_report({"meal_log_count": 2})

    assert result is None


def test_finalize_llm_report_adds_disclaimer_when_missing():
    report = WeeklyReportService._finalize_llm_report("이번 주에는 식단 기록과 챌린지 실천이 확인되었습니다.")

    assert REPORT_DISCLAIMER in report


@pytest.mark.asyncio
async def test_openai_report_client_rejects_non_ascii_api_key():
    client = OpenAIReportClient(
        api_key="sk-test—invalid",
        model_name="gpt-4o-mini",
        timeout_seconds=10,
    )

    with pytest.raises(ReportLLMError):
        await client.generate(source_summary={"meal_log_count": 1}, max_length=MAX_REPORT_TEXT_LENGTH)


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


def test_weekly_report_pdf_export_content_is_valid_pdf_bytes():
    report = SimpleNamespace(
        id=31,
        week_start_date=date(2026, 6, 1),
        week_end_date=date(2026, 6, 7),
        status="AVAILABLE",
        provider="RULE_BASED",
        report_text="이번 주 건강 기록은 총 3건 입력되었습니다.",
        summary_cards=[
            {"label": "건강 기록", "value": "3건", "status": "NORMAL", "description": "이번 주 입력 기록"},
        ],
        metric_summaries=[
            {"label": "식단", "value": "2", "unit": "건", "status": "NORMAL", "description": "식단 기록"},
        ],
    )

    content = WeeklyReportService._to_pdf_content(report)

    assert content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in content


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


def test_weekly_report_export_payload_contains_report_sections():
    report = SimpleNamespace(
        id=20,
        week_start_date=date(2026, 6, 1),
        week_end_date=date(2026, 6, 7),
        status="AVAILABLE",
        report_text="이번 주 리포트입니다.",
        source_summary={"meal_log_count": 2},
        summary_cards=[{"label": "식단 기록", "value": "2건", "status": "NORMAL", "description": "식단 기록 수"}],
        metric_summaries=[
            {"label": "식단", "value": "2", "unit": "건", "status": "NORMAL", "description": "식단 기록"}
        ],
        trend_summary={"status": "UNAVAILABLE", "message": "비교 없음"},
        challenge_summary={"checkin_count": 0, "completion_rate": 0, "status": "UNAVAILABLE", "message": "체크인 없음"},
        provider="RULE_BASED",
        model_name=RULE_BASED_MODEL,
        created_at=datetime(2026, 6, 7, 12, 0),
    )

    payload = WeeklyReportService._export_payload(report)
    csv_content = WeeklyReportService._to_csv_content(report)

    assert payload["report_id"] == 20
    assert payload["summary_cards"][0]["label"] == "식단 기록"
    assert "리포트 본문" in csv_content
    assert "이번 주 리포트입니다." in csv_content
