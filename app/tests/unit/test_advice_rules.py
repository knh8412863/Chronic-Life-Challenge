from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.dtos.advices import AdviceFeedbackType, AdviceTriggerType
from app.services.advices import ADVICE_TITLE, MAX_ADVICE_LENGTH, AdviceService
from app.services.home import HomeService
from app.services.llm_advice import OPENAI_PROVIDER, AdviceLLMError, AdviceLLMResult, OpenAIAdviceClient


def test_rule_based_advice_uses_prediction_and_metric_context():
    context = {
        "age": 45,
        "diagnosed_diseases": [],
        "at_risk_diseases": ["DIABETES"],
        "metric_assessment": {
            "obesity": {"status": "HIGH"},
            "dyslipidemia": {"status": "CAUTION"},
        },
    }

    advice = AdviceService._build_rule_based_advice(context)

    assert "당뇨 위험 신호" in advice
    assert "체중 관리" in advice
    assert "지질 수치 관리" in advice
    assert len(advice) <= MAX_ADVICE_LENGTH


def test_rule_based_advice_adds_shingles_consultation_for_older_chronic_patient():
    context = {
        "age": 65,
        "diagnosed_diseases": ["HYPERTENSION"],
        "at_risk_diseases": [],
        "metric_assessment": {
            "obesity": {"status": "NORMAL"},
            "dyslipidemia": {"status": "NORMAL"},
        },
    }

    advice = AdviceService._build_rule_based_advice(context)

    assert "대상포진 예방접종 상담" in advice


def test_prompt_summary_translates_risk_disease_names():
    context = {"at_risk_diseases": ["DIABETES", "CKD"]}

    assert AdviceService._prompt_summary(context) == "위험 신호: 당뇨, 만성신장질환"


def test_daily_advice_response_marks_existing_generation_state():
    advice = SimpleNamespace(
        id=10,
        advice_date=date(2026, 6, 2),
        advice_text="오늘은 건강 기록을 확인해 보세요.",
        provider="RULE_BASED",
        model_name="daily-advice-rules-v1",
        trigger_type="MANUAL",
        created_at=datetime(2026, 6, 2, 10, 30),
    )

    response = AdviceService._to_response(advice, generated=False)

    assert response.title == ADVICE_TITLE
    assert response.trigger_type == AdviceTriggerType.MANUAL
    assert response.generated is False
    assert response.source_type == "RULE_BASED"


def test_daily_advice_response_marks_openai_source_type():
    advice = SimpleNamespace(
        id=11,
        advice_date=date(2026, 6, 8),
        advice_text="오늘은 혈압 기록을 확인하고 가볍게 걸어보세요.",
        provider=OPENAI_PROVIDER,
        model_name="gpt-4o-mini",
        trigger_type="MANUAL",
        created_at=datetime(2026, 6, 8, 9, 0),
    )

    response = AdviceService._to_response(advice, generated=True)

    assert response.source_type == "LLM"
    assert response.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_generate_llm_advice_uses_openai_client_when_enabled(monkeypatch):
    class FakeOpenAIAdviceClient:
        is_configured = True

        def __init__(self, api_key: str | None, model_name: str, timeout_seconds: float) -> None:
            self.api_key = api_key
            self.model_name = model_name
            self.timeout_seconds = timeout_seconds

        async def generate(self, context: dict, prompt_summary: str, max_length: int) -> AdviceLLMResult:
            return AdviceLLMResult(
                advice_text="오늘은 혈당 기록을 확인하고 식후 10분 걷기를 실천해 보세요.",
                provider=OPENAI_PROVIDER,
                model_name=self.model_name,
                input_tokens=12,
                output_tokens=20,
                cache_read_tokens=3,
            )

    monkeypatch.setattr("app.services.advices.config.ADVICE_LLM_ENABLED", True)
    monkeypatch.setattr("app.services.advices.config.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.advices.config.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.advices.config.OPENAI_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("app.services.advices.OpenAIAdviceClient", FakeOpenAIAdviceClient)

    result = await AdviceService._generate_llm_advice({"at_risk_diseases": ["DIABETES"]})

    assert result is not None
    assert result.provider == OPENAI_PROVIDER
    assert result.model_name == "gpt-4o-mini"
    assert result.input_tokens == 12


@pytest.mark.asyncio
async def test_generate_llm_advice_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr("app.services.advices.config.ADVICE_LLM_ENABLED", False)

    result = await AdviceService._generate_llm_advice({"at_risk_diseases": ["DIABETES"]})

    assert result is None


@pytest.mark.asyncio
async def test_openai_advice_client_rejects_non_ascii_api_key():
    client = OpenAIAdviceClient(
        api_key="sk-test—invalid",
        model_name="gpt-4o-mini",
        timeout_seconds=10,
    )

    with pytest.raises(AdviceLLMError):
        await client.generate(
            context={"at_risk_diseases": []},
            prompt_summary="위험 신호 없음",
            max_length=MAX_ADVICE_LENGTH,
        )


def test_home_today_advice_uses_generated_advice_before_placeholder():
    advice = SimpleNamespace(id=3, advice_text="생성된 오늘의 조언")

    result = HomeService._build_today_advice(advice, latest_prediction=None)

    assert result.advice_id == 3
    assert result.content == "생성된 오늘의 조언"
    assert result.is_placeholder is False


def test_advice_feedback_response_uses_feedback_type_enum():
    feedback = SimpleNamespace(
        id=12,
        feedback_type="HELPFUL",
        created_at=datetime(2026, 6, 2, 11, 30),
    )

    response = AdviceService._to_feedback_response(feedback, advice_id=5)

    assert response.feedback_id == 12
    assert response.advice_id == 5
    assert response.feedback_type == AdviceFeedbackType.HELPFUL
