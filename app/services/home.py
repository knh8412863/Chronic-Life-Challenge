from datetime import date

from app.dtos.home import (
    HomeChallengeSummaryResponse,
    HomeHealthMetricSummaryResponse,
    HomeHealthRecordStatusResponse,
    HomeHealthScoreResponse,
    HomeRecentPredictionResponse,
    HomeSummaryResponse,
    HomeTodayAdviceResponse,
)
from app.dtos.predictions import MetricAssessmentResponse
from app.models.advices import LLMAdvice
from app.models.challenges import ChallengeParticipation
from app.models.predictions import (
    ChronicHealthInput,
    LipidObesityRecord,
    PredictionResult,
    RenalRecord,
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
        latest_health = await ChronicHealthInput.filter(user_id=user.id).order_by("-created_at").first()
        latest_lipid = await LipidObesityRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        latest_renal = await RenalRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        latest_prediction = (
            await PredictionResult.filter(user_id=user.id).order_by("-created_at").prefetch_related("items").first()
        )
        today_advice = await LLMAdvice.filter(user_id=user.id, advice_date=date.today()).order_by("-created_at").first()
        active_challenges = await ChallengeParticipation.filter(user_id=user.id, status="JOINED").prefetch_related(
            "challenge"
        )
        unread_notification_count = await NotificationService.count_unread(user.id)
        metric_assessment = await HealthInputService().get_metric_assessments(user)

        return HomeSummaryResponse(
            today_score=self._build_health_score(latest_health, latest_prediction, metric_assessment),
            recent_prediction=self._build_recent_prediction(latest_prediction),
            today_advice=self._build_today_advice(today_advice, latest_prediction),
            challenge_summary=self._build_challenge_summary(active_challenges),
            health_metric_summary=HomeHealthMetricSummaryResponse(
                dyslipidemia=metric_assessment.dyslipidemia,
                obesity=metric_assessment.obesity,
            ),
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
    ) -> HomeHealthScoreResponse:
        if latest_health is None:
            return HomeHealthScoreResponse(
                score=None,
                status="NEEDS_INPUT",
                message="건강 설문을 입력하면 오늘의 건강 점수를 확인할 수 있습니다.",
                calculation_basis=["건강 설문 미입력"],
            )

        score = 100
        basis = ["건강 설문 입력 완료"]

        if latest_prediction is not None:
            at_risk_count = sum(1 for item in latest_prediction.items if item.is_at_risk)
            if at_risk_count:
                score -= min(at_risk_count * 15, 45)
                basis.append(f"AI 예측 위험 신호 {at_risk_count}개")
            else:
                basis.append("최근 AI 예측 위험 신호 없음")
        else:
            score -= 10
            basis.append("AI 예측 결과 없음")

        for label, item in [
            ("고지혈증", metric_assessment.dyslipidemia),
            ("비만", metric_assessment.obesity),
        ]:
            if item.status == "HIGH":
                score -= 15
                basis.append(f"{label} 수치 위험")
            elif item.status == "CAUTION":
                score -= 8
                basis.append(f"{label} 수치 주의")
            elif item.status == "UNAVAILABLE":
                score -= 5
                basis.append(f"{label} 수치 미입력")

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
    def _build_today_advice(
        advice: LLMAdvice | None,
        latest_prediction: PredictionResult | None,
    ) -> HomeTodayAdviceResponse:
        if advice is not None:
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
