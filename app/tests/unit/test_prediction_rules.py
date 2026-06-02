from datetime import date
from types import SimpleNamespace

from app.dtos.predictions import MetricAssessmentItemResponse, MetricAssessmentResponse
from app.models.predictions import PredictionStatus
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


def test_ckd_risk_factors_use_renal_values_and_history():
    health = SimpleNamespace(diagnosed_diseases=["DIABETES"])
    renal = SimpleNamespace(creatinine=1.4, bun=22, urine_protein_pos=True)

    result = PredictionService._ckd_risk_factors(health, renal)

    assert "크레아티닌 수치가 높은 범위입니다." in result
    assert "BUN 수치가 높은 범위입니다." in result
    assert "소변 단백 양성으로 입력되었습니다." in result
    assert "당뇨 또는 고혈압 진단 이력이 입력되었습니다." in result


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
