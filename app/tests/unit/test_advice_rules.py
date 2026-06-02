from datetime import date, datetime
from types import SimpleNamespace

from app.dtos.advices import AdviceFeedbackType, AdviceTriggerType
from app.services.advices import ADVICE_TITLE, MAX_ADVICE_LENGTH, AdviceService
from app.services.home import HomeService


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
