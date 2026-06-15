from datetime import date

from app.dtos.home import (
    HomeChallengeSummaryResponse,
    HomeHealthMetricSummaryResponse,
    HomeHealthRecordStatusResponse,
    HomeHealthScoreResponse,
    HomeRecentPredictionResponse,
    HomeSummaryResponse,
    HomeTodayAdviceResponse,
    HomeVitalSummaryResponse,
)
from app.dtos.predictions import MetricAssessmentResponse
from app.models.advices import LLMAdvice
from app.models.challenges import ChallengeParticipation
from app.models.predictions import (
    ChronicHealthInput,
    LipidObesityRecord,
    PredictionResult,
    RenalRecord,
    VitalRecord,
)
from app.models.users import User
from app.services.notifications import NotificationService
from app.services.predictions import HealthInputService

DISEASE_LABELS = {
    "DIABETES": "당뇨",
    "HYPERTENSION": "고혈압",
    "CKD": "만성신장질환",
}


class HomeService:
    async def get_summary(self, user: User) -> HomeSummaryResponse:
        today = HealthInputService._today()
        latest_health = await ChronicHealthInput.filter(user_id=user.id).order_by("-created_at").first()
        latest_bp = (
            await VitalRecord.filter(user_id=user.id, measure_type__startswith="BP_")
            .order_by("-measured_at", "-created_at")
            .first()
        )
        latest_glucose = (
            await VitalRecord.filter(user_id=user.id, measure_type="GLUCOSE_FASTING")
            .order_by("-measured_at", "-created_at")
            .first()
        )
        latest_lipid = await LipidObesityRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        latest_renal = await RenalRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        latest_prediction = (
            await PredictionResult.filter(user_id=user.id).order_by("-created_at").prefetch_related("items").first()
        )
        today_bp = (
            await VitalRecord.filter(user_id=user.id, record_date=today, measure_type__startswith="BP_")
            .order_by("-measured_at", "-created_at")
            .first()
        )
        today_glucose = (
            await VitalRecord.filter(user_id=user.id, record_date=today, measure_type="GLUCOSE_FASTING")
            .order_by("-measured_at", "-created_at")
            .first()
        )
        today_advice = await LLMAdvice.filter(user_id=user.id, advice_date=today).order_by("-created_at").first()
        active_challenges = await ChallengeParticipation.filter(user_id=user.id, status="JOINED").prefetch_related(
            "challenge"
        )
        unread_notification_count = await NotificationService.count_unread(user.id)
        metric_assessment = await HealthInputService().get_metric_assessments(user)

        return HomeSummaryResponse(
            today_score=self._build_health_score(
                latest_health,
                latest_prediction,
                metric_assessment,
                latest_bp=latest_bp,
                latest_glucose=latest_glucose,
                latest_lipid=latest_lipid,
                latest_renal=latest_renal,
            ),
            recent_prediction=self._build_recent_prediction(latest_prediction),
            today_advice=self._build_today_advice(
                today_advice,
                latest_prediction,
                latest_today_record_at=self._latest_today_record_at(today_bp, today_glucose),
            ),
            challenge_summary=self._build_challenge_summary(active_challenges),
            health_metric_summary=HomeHealthMetricSummaryResponse(
                dyslipidemia=metric_assessment.dyslipidemia,
                obesity=metric_assessment.obesity,
            ),
            vital_summary=self._build_vital_summary(today_bp or latest_bp, today_glucose or latest_glucose, today),
            quick_record_status=HomeHealthRecordStatusResponse(
                has_health_survey=latest_health is not None,
                has_lipid_obesity_record=latest_lipid is not None,
                has_renal_record=latest_renal is not None,
                latest_health_input_at=latest_health.created_at if latest_health else None,
                latest_lipid_obesity_record_at=latest_lipid.created_at if latest_lipid else None,
                latest_renal_record_at=latest_renal.created_at if latest_renal else None,
            ),
            unread_notification_count=unread_notification_count,
        )

    @staticmethod
    def _latest_today_record_at(*records: VitalRecord | None) -> date | None:
        datetimes = [record.created_at for record in records if record is not None]
        return max(datetimes).date() if datetimes else None

    @staticmethod
    def _build_vital_summary(
        bp: VitalRecord | None,
        glucose: VitalRecord | None,
        today: date,
    ) -> HomeVitalSummaryResponse:
        bp_label, bp_status = HomeService._bp_label_status(bp)
        glucose_label, glucose_status = HomeService._glucose_label_status(glucose)
        return HomeVitalSummaryResponse(
            blood_pressure_label=bp_label,
            blood_pressure_status=bp_status,
            blood_pressure_value=f"{bp.sbp}/{bp.dbp} mmHg"
            if bp and bp.sbp is not None and bp.dbp is not None
            else None,
            glucose_label=glucose_label,
            glucose_status=glucose_status,
            glucose_value=f"{glucose.glucose} mg/dL" if glucose and glucose.glucose is not None else None,
            has_today_health_record=bool(
                (bp is not None and bp.record_date == today) or (glucose is not None and glucose.record_date == today)
            ),
        )

    @staticmethod
    def _bp_label_status(bp: VitalRecord | None) -> tuple[str, str]:
        if bp is None or bp.sbp is None or bp.dbp is None:
            return "미입력", "NEEDS_INPUT"
        if bp.sbp >= 140 or bp.dbp >= 90:
            return "심각", "HIGH"
        if bp.sbp < 120 and bp.dbp < 80:
            return "정상", "NORMAL"
        if bp.sbp <= 139 or bp.dbp <= 89:
            return "위험", "CAUTION"
        return "정상", "NORMAL"

    @staticmethod
    def _glucose_label_status(glucose: VitalRecord | None) -> tuple[str, str]:
        if glucose is None or glucose.glucose is None:
            return "미입력", "NEEDS_INPUT"
        if glucose.glucose >= 126:
            return "심각", "HIGH"
        if glucose.glucose >= 100:
            return "위험", "CAUTION"
        return "정상", "NORMAL"

    @staticmethod
    def _build_recent_prediction(result: PredictionResult | None) -> HomeRecentPredictionResponse | None:
        if result is None:
            return None

        at_risk_diseases = [
            DISEASE_LABELS.get(item.disease_code, item.disease_code) for item in result.items if item.is_at_risk
        ]
        return HomeRecentPredictionResponse(
            result_id=result.id,
            overall_risk_level=result.overall_risk_level,
            at_risk_diseases=at_risk_diseases,
            created_at=result.created_at,
        )

    @staticmethod
    def _build_health_score(
        latest_health: ChronicHealthInput | None,
        latest_prediction: PredictionResult | None,
        metric_assessment: MetricAssessmentResponse,
        latest_bp: VitalRecord | None = None,
        latest_glucose: VitalRecord | None = None,
        latest_lipid: LipidObesityRecord | None = None,
        latest_renal: RenalRecord | None = None,
    ) -> HomeHealthScoreResponse:
        has_health_record = any([latest_health, latest_bp, latest_glucose, latest_lipid, latest_renal])
        if not has_health_record:
            return HomeHealthScoreResponse(
                score=None,
                status="NEEDS_INPUT",
                message="건강 수치를 기록하면 오늘의 건강 점수를 확인할 수 있습니다.",
                calculation_basis=["건강 수치 미입력"],
            )

        score = 100
        basis = ["건강 설문 입력 완료"] if latest_health else ["건강 수치 입력 완료"]

        for penalty, reasons in [
            HomeService._prediction_score_adjustment(latest_prediction),
            HomeService._metric_score_adjustment(metric_assessment),
            HomeService._latest_vital_score_adjustment(latest_bp, latest_glucose),
            HomeService._renal_score_adjustment(latest_renal),
        ]:
            score -= penalty
            basis.extend(reasons)

        score = max(score, 0)
        if score < 60:
            status = "HIGH"
            message = "주의가 필요한 건강 신호가 있습니다."
        elif score < 80:
            status = "CAUTION"
            message = "일부 건강 지표를 점검해 보세요."
        else:
            status = "GOOD"
            message = "현재 입력 기준 건강 상태가 양호한 편입니다."

        return HomeHealthScoreResponse(
            score=score,
            status=status,
            message=message,
            calculation_basis=basis,
        )

    @staticmethod
    def _prediction_score_adjustment(latest_prediction: PredictionResult | None) -> tuple[int, list[str]]:
        if latest_prediction is None:
            return 10, ["AI 예측 결과 없음"]

        at_risk_count = sum(1 for item in latest_prediction.items if item.is_at_risk)
        if at_risk_count:
            return min(at_risk_count * 15, 45), [f"AI 예측 위험 신호 {at_risk_count}개"]
        return 0, ["최근 AI 예측 위험 신호 없음"]

    @staticmethod
    def _metric_score_adjustment(metric_assessment: MetricAssessmentResponse) -> tuple[int, list[str]]:
        penalty = 0
        reasons: list[str] = []
        for label, item in [
            ("고지혈증", metric_assessment.dyslipidemia),
            ("비만", metric_assessment.obesity),
        ]:
            item_penalty, reason = HomeService._metric_item_adjustment(label, item.status)
            penalty += item_penalty
            if reason:
                reasons.append(reason)
        return penalty, reasons

    @staticmethod
    def _metric_item_adjustment(label: str, status: str) -> tuple[int, str | None]:
        if status == "HIGH":
            return 15, f"{label} 수치 위험"
        if status == "CAUTION":
            return 8, f"{label} 수치 주의"
        if status == "UNAVAILABLE":
            return 5, f"{label} 수치 미입력"
        return 0, None

    @staticmethod
    def _latest_vital_score_adjustment(
        latest_bp: VitalRecord | None,
        latest_glucose: VitalRecord | None,
    ) -> tuple[int, list[str]]:
        bp_penalty, bp_reason = HomeService._bp_score_adjustment(latest_bp)
        glucose_penalty, glucose_reason = HomeService._glucose_score_adjustment(latest_glucose)
        reasons = [reason for reason in [bp_reason, glucose_reason] if reason]
        return bp_penalty + glucose_penalty, reasons

    @staticmethod
    def _bp_score_adjustment(latest_bp: VitalRecord | None) -> tuple[int, str | None]:
        if latest_bp is None or latest_bp.sbp is None or latest_bp.dbp is None:
            return 0, None
        if latest_bp.sbp >= 140 or latest_bp.dbp >= 90:
            return 15, "최근 혈압 수치 심각"
        if latest_bp.sbp < 120 and latest_bp.dbp < 80:
            return 0, "최근 혈압 수치 정상"
        if latest_bp.sbp <= 139 or latest_bp.dbp <= 89:
            return 8, "최근 혈압 수치 위험"
        return 0, "최근 혈압 수치 정상"

    @staticmethod
    def _glucose_score_adjustment(latest_glucose: VitalRecord | None) -> tuple[int, str | None]:
        if latest_glucose is None or latest_glucose.glucose is None:
            return 0, None
        if latest_glucose.glucose >= 126:
            return 15, "최근 공복혈당 수치 심각"
        if latest_glucose.glucose >= 100:
            return 8, "최근 공복혈당 수치 위험"
        return 0, "최근 공복혈당 수치 정상"

    @staticmethod
    def _renal_score_adjustment(latest_renal: RenalRecord | None) -> tuple[int, list[str]]:
        if latest_renal is None:
            return 0, []

        egfr = float(latest_renal.egfr) if latest_renal.egfr is not None else None
        creatinine = float(latest_renal.creatinine) if latest_renal.creatinine is not None else None
        has_risk = (
            (egfr is not None and egfr < 60)
            or (creatinine is not None and creatinine >= 1.3)
            or latest_renal.urine_protein_pos
        )
        if has_risk:
            return 15, ["최근 신장 지표 위험"]
        if egfr is not None or creatinine is not None or latest_renal.urine_protein_pos is not None:
            return 0, ["최근 신장 지표 입력 완료"]
        return 0, []

    @staticmethod
    def _build_today_advice(
        advice: LLMAdvice | None,
        latest_prediction: PredictionResult | None,
        latest_today_record_at: date | None = None,
    ) -> HomeTodayAdviceResponse:
        if advice is not None:
            if latest_today_record_at is not None and advice.created_at.date() < latest_today_record_at:
                return HomeTodayAdviceResponse(
                    title="오늘의 건강 조언",
                    content="오늘 입력한 건강 수치를 확인했습니다. 오늘의 조언 화면에서 새로 받기를 누르면 최신 기록 기준으로 조언을 받을 수 있습니다.",
                    is_placeholder=True,
                )
            return HomeTodayAdviceResponse(
                advice_id=advice.id,
                title="오늘의 건강 조언",
                content=advice.advice_text,
                is_placeholder=False,
            )

        if latest_prediction and latest_prediction.overall_risk_level == "HIGH":
            return HomeTodayAdviceResponse(
                title="오늘의 건강 조언",
                content="최근 예측 결과에서 위험 신호가 확인되었습니다. 혈압·혈당 기록을 확인하고 필요하면 전문의와 상담해 보세요.",
            )

        return HomeTodayAdviceResponse(
            title="오늘의 건강 조언",
            content="오늘의 건강 기록을 입력하면 더 개인화된 조언을 받을 수 있습니다.",
        )

    @staticmethod
    def _build_challenge_summary(participations: list[ChallengeParticipation]) -> HomeChallengeSummaryResponse:
        active_count = len(participations)
        if active_count == 0:
            return HomeChallengeSummaryResponse(
                active_count=0,
                completion_rate=0.0,
                message="참여 중인 챌린지가 없습니다.",
            )

        rates = [
            HomeService._challenge_completion_rate(item.progress_count, item.challenge.duration_days)
            for item in participations
        ]
        average_rate = round(sum(rates) / active_count, 1)
        return HomeChallengeSummaryResponse(
            active_count=active_count,
            completion_rate=average_rate,
            message=f"진행 중인 챌린지 {active_count}개가 있습니다.",
        )

    @staticmethod
    def _challenge_completion_rate(progress_count: int, duration_days: int) -> float:
        if duration_days <= 0:
            return 0.0
        return round(min(progress_count / duration_days, 1.0) * 100, 1)
