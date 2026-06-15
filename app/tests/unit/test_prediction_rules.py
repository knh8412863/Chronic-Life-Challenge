from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.dtos.predictions import MetricAssessmentItemResponse, MetricAssessmentResponse
from app.models.predictions import PredictionMode, PredictionStatus
from app.models.users import Gender
from app.services.home import HomeService
from app.services.predictions import HealthInputService, PredictionService, _calculate_age, _calculate_bmi


def test_calculate_bmi_rounds_to_two_decimal_places():
    assert _calculate_bmi(160, 67) == 26.17


def test_calculate_age_uses_birth_month_and_day():
    assert _calculate_age(date(1990, 6, 2), today=date(2026, 6, 1)) == 35
    assert _calculate_age(date(1990, 6, 2), today=date(2026, 6, 2)) == 36


def test_prediction_progress_mapping():
    assert PredictionService._task_progress(PredictionStatus.PENDING) == (0, "예측 요청 접수")
    assert PredictionService._task_progress(PredictionStatus.SUCCESS) == (100, "예측 완료")


def test_prediction_result_list_item_uses_highest_probability_and_feedback_state():
    result = SimpleNamespace(
        id=3,
        task=SimpleNamespace(prediction_mode=PredictionMode.SCREENING),
        created_at=datetime(2026, 6, 9, 12, 0, 0),
        overall_risk_level="LOW",
        input_completeness={"used_default_values": False, "missing_fields": [], "message": "입력값 반영"},
        items=[
            SimpleNamespace(
                disease_code="DIABETES",
                probability=Decimal("0.120000"),
                threshold=Decimal("0.05500"),
                is_at_risk=True,
                risk_level="HIGH",
                message="당뇨 위험 신호가 감지되었습니다.",
                risk_factors=["공복혈당이 당뇨 의심 기준 이상입니다."],
            ),
            SimpleNamespace(
                disease_code="HYPERTENSION",
                probability=Decimal("0.050000"),
                threshold=Decimal("0.09600"),
                is_at_risk=False,
                risk_level="LOW",
                message="고혈압 위험 신호는 현재 기준에서 높지 않습니다.",
                risk_factors=[],
            ),
        ],
    )

    item = PredictionService()._to_result_list_item(result, feedback_result_ids={3})

    assert item.result_id == 3
    assert item.overall_risk_level == "HIGH"
    assert item.highest_risk_disease == "diabetes"
    assert item.highest_risk_probability == 0.12
    assert item.highest_risk_score == 0.8
    assert item.feedback_submitted is True
    assert set(item.disease_risks) == {"diabetes", "hypertension"}


def test_dyslipidemia_assessment_detects_high_ldl_and_low_hdl():
    user = SimpleNamespace(gender=Gender.FEMALE)
    lipid = SimpleNamespace(
        total_cholesterol=230,
        hdl_cholesterol=45,
        ldl_cholesterol=165,
        triglycerides=180,
    )

    result = HealthInputService._assess_dyslipidemia(user, lipid)

    assert result.status == "HIGH"
    assert "LDL 콜레스테롤이 위험 범위입니다." in result.reasons
    assert "HDL 콜레스테롤이 낮은 범위입니다." in result.reasons
    assert result.missing_fields == []


def test_obesity_assessment_uses_bmi_and_waist_threshold():
    user = SimpleNamespace(gender=Gender.FEMALE)
    profile = SimpleNamespace(bmi=24.5)
    health = SimpleNamespace(bmi=24.5, waist_circumference=88)

    result = HealthInputService._assess_obesity(user, profile, health, lipid=None)

    assert result.status == "HIGH"
    assert "BMI가 과체중 범위입니다." in result.reasons
    assert "허리둘레가 복부비만 기준 이상입니다." in result.reasons


def test_diabetes_risk_factors_use_input_values():
    health = SimpleNamespace(
        glucose_fasting=130,
        bmi=26,
        waist_circumference=80,
        gender=Gender.FEMALE,
        fh_diabetes_father=False,
        fh_diabetes_mother=True,
        fh_diabetes_sibling=False,
    )
    lifestyle = SimpleNamespace(walking_days=2)

    result = PredictionService._diabetes_risk_factors(health, lifestyle, lipid=None)

    assert "공복혈당이 당뇨 의심 기준 이상입니다." in result
    assert "BMI가 비만 범위입니다." in result
    assert "당뇨 가족력이 입력되었습니다." in result
    assert "주간 걷기 일수가 낮은 편입니다." in result


def test_diabetes_risk_factors_mark_borderline_fasting_glucose():
    health = SimpleNamespace(
        glucose_fasting=120,
        bmi=22,
        waist_circumference=80,
        gender=Gender.FEMALE,
        fh_diabetes_father=False,
        fh_diabetes_mother=False,
        fh_diabetes_sibling=False,
    )
    lifestyle = SimpleNamespace(walking_days=5)

    result = PredictionService._diabetes_risk_factors(health, lifestyle, lipid=None)

    assert "공복혈당이 경계 범위입니다." in result
    assert "공복혈당이 당뇨 의심 기준 이상입니다." not in result


def test_ckd_risk_factors_use_renal_values_and_history():
    health = SimpleNamespace(diagnosed_diseases=["DIABETES"])
    renal = SimpleNamespace(creatinine=1.4, bun=22, urine_protein_pos=True)

    result = PredictionService._ckd_risk_factors(health, renal)

    assert "크레아티닌 수치가 높은 범위입니다." in result
    assert "BUN 수치가 높은 범위입니다." in result
    assert "소변 단백 양성으로 입력되었습니다." in result
    assert "당뇨 또는 고혈압 진단 이력이 입력되었습니다." in result


def test_clinical_risk_override_marks_severe_hypertension_as_high_risk():
    values = {
        "probability": Decimal("0.030000"),
        "threshold": Decimal("0.09600"),
        "is_at_risk": False,
        "risk_level": "LOW",
        "message": "고혈압 위험 신호는 현재 기준에서 높지 않습니다.",
        "risk_factors": ["수축기 혈압이 높은 범위입니다.", "이완기 혈압이 높은 범위입니다."],
    }

    PredictionService._apply_clinical_risk_overrides("HYPERTENSION", values)

    assert values["probability"] == Decimal("0.030000")
    assert values["is_at_risk"] is True
    assert values["risk_level"] == "HIGH"
    assert PredictionService._display_risk_score(values) == 0.8


def test_clinical_risk_override_marks_diabetes_fasting_glucose_as_high_risk():
    values = {
        "probability": Decimal("0.009000"),
        "threshold": Decimal("0.05500"),
        "is_at_risk": False,
        "risk_level": "LOW",
        "message": "당뇨 위험 신호는 현재 기준에서 높지 않습니다.",
        "risk_factors": ["공복혈당이 당뇨 의심 기준 이상입니다."],
    }

    PredictionService._apply_clinical_risk_overrides("DIABETES", values)

    assert values["probability"] == Decimal("0.009000")
    assert values["is_at_risk"] is True
    assert values["risk_level"] == "HIGH"
    assert PredictionService._display_risk_score(values) == 0.8


def test_clinical_risk_override_marks_borderline_fasting_glucose_as_medium_risk():
    values = {
        "probability": Decimal("0.009000"),
        "threshold": Decimal("0.05500"),
        "is_at_risk": False,
        "risk_level": "LOW",
        "message": "당뇨 위험 신호는 현재 기준에서 높지 않습니다.",
        "risk_factors": ["공복혈당이 경계 범위입니다."],
    }

    PredictionService._apply_clinical_risk_overrides("DIABETES", values)

    assert values["probability"] == Decimal("0.009000")
    assert values["is_at_risk"] is True
    assert values["risk_level"] == "MEDIUM"
    assert PredictionService._display_risk_score(values) == 0.45


def test_clinical_risk_override_does_not_mark_hypertension_by_bmi_only():
    values = {
        "probability": Decimal("0.030000"),
        "threshold": Decimal("0.09600"),
        "is_at_risk": False,
        "risk_level": "LOW",
        "message": "고혈압 위험 신호는 현재 기준에서 높지 않습니다.",
        "risk_factors": ["BMI가 비만 범위입니다.", "허리둘레가 복부비만 기준 이상입니다."],
    }

    PredictionService._apply_clinical_risk_overrides("HYPERTENSION", values)

    assert values["probability"] == Decimal("0.030000")
    assert values["is_at_risk"] is False
    assert values["risk_level"] == "LOW"


def test_overall_risk_level_uses_highest_clinical_level():
    result = PredictionService._overall_risk_level(
        {
            "DIABETES": {"risk_level": "LOW"},
            "HYPERTENSION": {"risk_level": "MEDIUM"},
            "CKD": {"risk_level": "LOW"},
        }
    )

    assert result == "MEDIUM"


def test_prediction_model_input_uses_latest_lipid_obesity_body_values():
    raw = {"height": 165.0, "weight": 63.0, "bmi": 23.14, "waist_circumference": 78.0}
    lipid = SimpleNamespace(
        height_cm=Decimal("166.5"),
        weight_kg=Decimal("67.2"),
        bmi=Decimal("24.24"),
        waist_circumference=Decimal("82.0"),
    )

    PredictionService._apply_lipid_obesity_model_overrides(raw, lipid)

    assert raw["height"] == 166.5
    assert raw["weight"] == 67.2
    assert raw["bmi"] == 24.24
    assert raw["waist_circumference"] == 82.0


def test_health_score_penalizes_missing_prediction_and_metric_inputs():
    metric_assessment = MetricAssessmentResponse(
        dyslipidemia=MetricAssessmentItemResponse(status="UNAVAILABLE", reasons=[], missing_fields=[]),
        obesity=MetricAssessmentItemResponse(status="HIGH", reasons=[], missing_fields=[]),
    )

    score = HomeService._build_health_score(
        latest_health=SimpleNamespace(),
        latest_prediction=None,
        metric_assessment=metric_assessment,
    )

    assert score.score == 70
    assert score.status == "CAUTION"
    assert "AI 예측 결과 없음" in score.calculation_basis
    assert "비만 수치 위험" in score.calculation_basis


def test_health_score_can_use_latest_vitals_without_health_survey():
    metric_assessment = MetricAssessmentResponse(
        dyslipidemia=MetricAssessmentItemResponse(status="UNAVAILABLE", reasons=[], missing_fields=[]),
        obesity=MetricAssessmentItemResponse(status="UNAVAILABLE", reasons=[], missing_fields=[]),
    )

    score = HomeService._build_health_score(
        latest_health=None,
        latest_prediction=None,
        metric_assessment=metric_assessment,
        latest_bp=SimpleNamespace(sbp=145, dbp=92),
    )

    assert score.score is not None
    assert score.status == "CAUTION"
    assert "건강 수치 입력 완료" in score.calculation_basis
    assert "최근 혈압 수치 심각" in score.calculation_basis


@pytest.mark.asyncio
async def test_prediction_snapshot_record_loader_rejects_unowned_health_record(monkeypatch):
    class MissingRecord:
        @staticmethod
        async def get_or_none(**kwargs):
            return None

    class ExistingRecord:
        @staticmethod
        async def get_or_none(**kwargs):
            return SimpleNamespace(id=kwargs["id"], user_id=kwargs["user_id"])

    monkeypatch.setattr("app.services.predictions.ChronicHealthInput", MissingRecord)
    monkeypatch.setattr("app.services.predictions.LifestyleInput", ExistingRecord)

    snapshot = SimpleNamespace(
        chronic_health_input_id=10,
        lifestyle_input_id=20,
        lipid_obesity_record_id=None,
        renal_record_id=None,
    )

    with pytest.raises(ValueError, match="예측 입력 소유자 검증"):
        await PredictionService._load_owned_snapshot_records(snapshot, user_id=1)


@pytest.mark.asyncio
async def test_prediction_snapshot_record_loader_rejects_unowned_optional_records(monkeypatch):
    class ExistingRecord:
        @staticmethod
        async def get_or_none(**kwargs):
            return SimpleNamespace(id=kwargs["id"], user_id=kwargs["user_id"])

    class MissingRecord:
        @staticmethod
        async def get_or_none(**kwargs):
            return None

    monkeypatch.setattr("app.services.predictions.ChronicHealthInput", ExistingRecord)
    monkeypatch.setattr("app.services.predictions.LifestyleInput", ExistingRecord)
    monkeypatch.setattr("app.services.predictions.LipidObesityRecord", MissingRecord)

    snapshot = SimpleNamespace(
        chronic_health_input_id=10,
        lifestyle_input_id=20,
        lipid_obesity_record_id=30,
        renal_record_id=None,
    )

    with pytest.raises(ValueError, match="예측 입력 소유자 검증"):
        await PredictionService._load_owned_snapshot_records(snapshot, user_id=1)
