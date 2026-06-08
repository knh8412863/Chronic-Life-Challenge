from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status

from app.core import config, default_logger
from app.dtos.reports import (
    CurrentWeeklyReportResponse,
    WeeklyReportChallengeSummaryResponse,
    WeeklyReportGenerateRequest,
    WeeklyReportListItemResponse,
    WeeklyReportMetricSummaryResponse,
    WeeklyReportResponse,
    WeeklyReportSourceSummaryResponse,
    WeeklyReportSummaryCardResponse,
    WeeklyReportTrendSummaryResponse,
)
from app.models.challenges import ChallengeCheckin
from app.models.predictions import (
    ActivityLog,
    ChronicHealthInput,
    ExerciseLog,
    LipidObesityRecord,
    MealLog,
    PredictionResult,
    RenalRecord,
    VitalRecord,
)
from app.models.reports import WeeklyReport
from app.models.users import User
from app.services.llm_advice import OPENAI_PROVIDER
from app.services.llm_report import OpenAIReportClient, ReportLLMError, ReportLLMResult

RULE_BASED_PROVIDER = "RULE_BASED"
RULE_BASED_MODEL = "weekly-report-rules-v1"
MAX_REPORT_TEXT_LENGTH = 600


class WeeklyReportService:
    async def generate_current_week(self, user: User, data: WeeklyReportGenerateRequest) -> WeeklyReportResponse:
        week_start, week_end = self._week_range()
        existing = await WeeklyReport.get_or_none(user_id=user.id, week_start_date=week_start)
        if existing and not data.force_regenerate:
            return self._to_response(existing, generated=False)
        if existing and data.force_regenerate:
            await existing.delete()

        source_summary = await self._build_source_summary(user.id, week_start, week_end)
        llm_result = await self._generate_llm_report(source_summary)
        report_text = llm_result.report_text if llm_result else self._build_report_text(source_summary)
        report = await WeeklyReport.create(
            user=user,
            week_start_date=week_start,
            week_end_date=week_end,
            status="AVAILABLE",
            source_summary=source_summary,
            summary_cards=self._build_summary_cards(source_summary),
            metric_summaries=self._build_metric_summaries(source_summary),
            trend_summary=self._build_trend_summary(None),
            challenge_summary=self._build_challenge_summary(source_summary),
            report_text=report_text,
            provider=llm_result.provider if llm_result else RULE_BASED_PROVIDER,
            model_name=llm_result.model_name if llm_result else RULE_BASED_MODEL,
            input_tokens=llm_result.input_tokens if llm_result else 0,
            output_tokens=llm_result.output_tokens if llm_result else 0,
            cache_read_tokens=llm_result.cache_read_tokens if llm_result else 0,
        )
        return self._to_response(report, generated=True)

    async def get_current_week(self, user: User) -> CurrentWeeklyReportResponse:
        week_start, week_end = self._week_range()
        report = await WeeklyReport.get_or_none(user_id=user.id, week_start_date=week_start)
        if report:
            return CurrentWeeklyReportResponse(
                status="AVAILABLE",
                week_start_date=week_start,
                week_end_date=week_end,
                report=self._to_response(report, generated=False),
            )

        source_summary = await self._build_source_summary(user.id, week_start, week_end)
        if self._has_report_source_data(source_summary):
            return CurrentWeeklyReportResponse(
                status="GENERATABLE",
                week_start_date=week_start,
                week_end_date=week_end,
                empty_message="이번 주 건강 데이터로 리포트를 생성할 수 있습니다.",
            )

        return CurrentWeeklyReportResponse(
            status="EMPTY",
            week_start_date=week_start,
            week_end_date=week_end,
            empty_message="이번 주 리포트를 만들 건강 데이터가 아직 없습니다.",
        )

    async def get_report(self, user: User, report_id: int) -> WeeklyReportResponse:
        report = await WeeklyReport.get_or_none(id=report_id, user_id=user.id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주간 리포트를 찾을 수 없습니다.")
        return self._to_response(report, generated=False)

    async def get_reports(self, user: User, limit: int = 20) -> list[WeeklyReportListItemResponse]:
        reports = await WeeklyReport.filter(user_id=user.id).order_by("-week_start_date").limit(limit)
        return [self._to_list_item(report) for report in reports]

    @staticmethod
    async def _build_source_summary(user_id: int, week_start: date, week_end: date) -> dict[str, int]:
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end + timedelta(days=1), time.min)
        health_survey_count = await ChronicHealthInput.filter(
            user_id=user_id,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
        ).count()
        lipid_obesity_record_count = await LipidObesityRecord.filter(
            user_id=user_id,
            record_date__gte=week_start,
            record_date__lte=week_end,
        ).count()
        renal_record_count = await RenalRecord.filter(
            user_id=user_id,
            record_date__gte=week_start,
            record_date__lte=week_end,
        ).count()
        vital_record_count = await VitalRecord.filter(
            user_id=user_id,
            record_date__gte=week_start,
            record_date__lte=week_end,
        ).count()
        activity_log_count = await ActivityLog.filter(
            user_id=user_id,
            record_date__gte=week_start,
            record_date__lte=week_end,
        ).count()
        exercise_log_count = await ExerciseLog.filter(
            user_id=user_id,
            exercise_date__gte=week_start,
            exercise_date__lte=week_end,
        ).count()
        meal_log_count = await MealLog.filter(
            user_id=user_id,
            meal_date__gte=week_start,
            meal_date__lte=week_end,
        ).count()
        predictions = (
            await PredictionResult.filter(user_id=user_id, created_at__gte=start_dt, created_at__lt=end_dt)
            .order_by("-created_at")
            .prefetch_related("items")
        )
        challenge_checkin_count = await ChallengeCheckin.filter(
            user_id=user_id,
            checkin_date__gte=week_start,
            checkin_date__lte=week_end,
        ).count()
        return {
            "health_survey_count": health_survey_count,
            "lipid_obesity_record_count": lipid_obesity_record_count,
            "renal_record_count": renal_record_count,
            "vital_record_count": vital_record_count,
            "activity_log_count": activity_log_count,
            "exercise_log_count": exercise_log_count,
            "meal_log_count": meal_log_count,
            "prediction_count": len(predictions),
            "at_risk_prediction_count": sum(
                1 for prediction in predictions if any(item.is_at_risk for item in prediction.items)
            ),
            "challenge_checkin_count": challenge_checkin_count,
        }

    @staticmethod
    def _has_report_source_data(source_summary: dict[str, int]) -> bool:
        return any(
            source_summary.get(field, 0) > 0
            for field in [
                "health_survey_count",
                "lipid_obesity_record_count",
                "renal_record_count",
                "vital_record_count",
                "activity_log_count",
                "exercise_log_count",
                "meal_log_count",
                "prediction_count",
                "challenge_checkin_count",
            ]
        )

    @staticmethod
    def _build_report_text(source_summary: dict[str, int]) -> str:
        total_health_records = (
            source_summary["health_survey_count"]
            + source_summary["lipid_obesity_record_count"]
            + source_summary["renal_record_count"]
            + source_summary.get("vital_record_count", 0)
        )
        parts = []
        if total_health_records == 0:
            parts.append(
                "이번 주에는 건강 기록이 아직 없습니다. 다음 주 리포트를 위해 혈압·혈당 또는 검사 수치를 입력해 보세요."
            )
        else:
            parts.append(f"이번 주 건강 기록은 총 {total_health_records}건 입력되었습니다.")

        if source_summary["prediction_count"] == 0:
            parts.append("AI 예측 결과가 없어 위험 변화는 판단하지 않았습니다.")
        elif source_summary["at_risk_prediction_count"] > 0:
            parts.append(
                f"AI 예측 중 위험 신호가 포함된 결과가 {source_summary['at_risk_prediction_count']}건 있습니다."
            )
        else:
            parts.append("AI 예측 결과에서 높은 위험 신호는 확인되지 않았습니다.")

        if source_summary["challenge_checkin_count"] == 0:
            parts.append("챌린지 체크인이 없어 생활습관 실천 기록이 부족합니다.")
        else:
            parts.append(f"챌린지는 {source_summary['challenge_checkin_count']}회 체크인했습니다.")

        parts.append("본 리포트는 의료 진단이 아닌 생활습관 점검용 참고 자료입니다.")
        return " ".join(parts)

    @staticmethod
    async def _generate_llm_report(source_summary: dict[str, int]) -> ReportLLMResult | None:
        if not config.REPORT_LLM_ENABLED:
            default_logger.info("weekly report llm disabled; using rule-based report")
            return None

        client = OpenAIReportClient(
            api_key=config.OPENAI_API_KEY,
            model_name=config.OPENAI_MODEL,
            timeout_seconds=config.OPENAI_TIMEOUT_SECONDS,
        )
        if not client.is_configured:
            default_logger.warning("weekly report llm api key is not configured; using rule-based report")
            return None

        try:
            result = await client.generate(source_summary=source_summary, max_length=MAX_REPORT_TEXT_LENGTH)
        except ReportLLMError:
            default_logger.exception("weekly report llm generation failed; using rule-based report")
            return None

        return ReportLLMResult(
            report_text=WeeklyReportService._limit_text(result.report_text, MAX_REPORT_TEXT_LENGTH),
            provider=result.provider,
            model_name=result.model_name,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cache_read_tokens=result.cache_read_tokens,
        )

    @staticmethod
    def _build_summary_cards(source_summary: dict[str, int]) -> list[dict[str, str]]:
        total_health_records = WeeklyReportService._total_health_records(source_summary)
        at_risk_count = source_summary.get("at_risk_prediction_count", 0)
        meal_count = source_summary.get("meal_log_count", 0)
        exercise_count = source_summary.get("exercise_log_count", 0)
        challenge_count = source_summary.get("challenge_checkin_count", 0)
        return [
            {
                "label": "건강 기록",
                "value": f"{total_health_records}건",
                "status": "NORMAL" if total_health_records > 0 else "UNAVAILABLE",
                "description": "이번 주 입력된 건강 데이터 수입니다.",
            },
            {
                "label": "AI 위험 신호",
                "value": f"{at_risk_count}건",
                "status": "HIGH" if at_risk_count > 0 else "NORMAL",
                "description": "이번 주 예측 결과 중 위험 신호가 포함된 건수입니다.",
            },
            {
                "label": "식단 기록",
                "value": f"{meal_count}건",
                "status": "NORMAL" if meal_count > 0 else "UNAVAILABLE",
                "description": "이번 주 저장한 식단 기록 수입니다.",
            },
            {
                "label": "운동 기록",
                "value": f"{exercise_count}건",
                "status": "NORMAL" if exercise_count > 0 else "UNAVAILABLE",
                "description": "이번 주 저장한 운동 기록 수입니다.",
            },
            {
                "label": "챌린지",
                "value": f"{challenge_count}회",
                "status": "NORMAL" if challenge_count >= 3 else "CAUTION" if challenge_count > 0 else "UNAVAILABLE",
                "description": "이번 주 챌린지 체크인 횟수입니다.",
            },
        ]

    @staticmethod
    def _build_metric_summaries(source_summary: dict[str, int]) -> list[dict[str, str]]:
        return [
            WeeklyReportService._metric_summary(
                "VITAL_RECORDS",
                "혈압·혈당",
                source_summary.get("vital_record_count", 0),
                "건",
                "혈압·혈당 기록 입력 횟수입니다.",
            ),
            WeeklyReportService._metric_summary(
                "MEAL_LOGS",
                "식단",
                source_summary.get("meal_log_count", 0),
                "건",
                "식단 기록 입력 횟수입니다.",
            ),
            WeeklyReportService._metric_summary(
                "EXERCISE_LOGS",
                "운동",
                source_summary.get("exercise_log_count", 0),
                "건",
                "운동 기록 입력 횟수입니다.",
            ),
            WeeklyReportService._metric_summary(
                "ACTIVITY_LOGS",
                "생활습관",
                source_summary.get("activity_log_count", 0),
                "건",
                "생활습관 기록 입력 횟수입니다.",
            ),
            WeeklyReportService._metric_summary(
                "CHALLENGE_CHECKINS",
                "챌린지",
                source_summary.get("challenge_checkin_count", 0),
                "회",
                "챌린지 실천 체크인 횟수입니다.",
            ),
        ]

    @staticmethod
    def _metric_summary(metric: str, label: str, count: int, unit: str, description: str) -> dict[str, str]:
        return {
            "metric": metric,
            "label": label,
            "value": str(count),
            "unit": unit,
            "status": "NORMAL" if count > 0 else "UNAVAILABLE",
            "description": description,
        }

    @staticmethod
    def _build_trend_summary(previous_report: WeeklyReport | None) -> dict[str, str | int | None]:
        if previous_report is None:
            return {
                "status": "UNAVAILABLE",
                "message": "전주 리포트가 없어 추이 비교는 제공하지 않습니다.",
                "previous_week_report_id": None,
            }
        return {
            "status": "UNCHANGED",
            "message": "전주 대비 상세 추이 비교는 추후 고도화 예정입니다.",
            "previous_week_report_id": previous_report.id,
        }

    @staticmethod
    def _build_challenge_summary(source_summary: dict[str, int]) -> dict[str, str | int | float]:
        checkin_count = source_summary.get("challenge_checkin_count", 0)
        completion_rate = round(min(checkin_count / 7, 1.0) * 100, 1)
        if checkin_count == 0:
            status_value = "UNAVAILABLE"
            message = "이번 주 챌린지 체크인이 없습니다."
        elif completion_rate >= 100:
            status_value = "ACHIEVED"
            message = "이번 주 챌린지를 매일 실천했습니다."
        else:
            status_value = "IN_PROGRESS"
            message = f"이번 주 챌린지를 {checkin_count}회 실천했습니다."
        return {
            "checkin_count": checkin_count,
            "completion_rate": completion_rate,
            "status": status_value,
            "message": message,
        }

    @staticmethod
    def _total_health_records(source_summary: dict[str, int]) -> int:
        return (
            source_summary.get("health_survey_count", 0)
            + source_summary.get("lipid_obesity_record_count", 0)
            + source_summary.get("renal_record_count", 0)
            + source_summary.get("vital_record_count", 0)
        )

    @staticmethod
    def _week_range(today: date | None = None) -> tuple[date, date]:
        current = today or date.today()
        week_start = current - timedelta(days=current.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    @staticmethod
    def _to_response(report: WeeklyReport, generated: bool) -> WeeklyReportResponse:
        return WeeklyReportResponse(
            report_id=report.id,
            week_start_date=report.week_start_date,
            week_end_date=report.week_end_date,
            status=report.status,
            source_summary=WeeklyReportSourceSummaryResponse(**report.source_summary),
            summary_cards=[WeeklyReportSummaryCardResponse(**item) for item in report.summary_cards],
            metric_summaries=[WeeklyReportMetricSummaryResponse(**item) for item in report.metric_summaries],
            trend_summary=WeeklyReportTrendSummaryResponse(**report.trend_summary),
            challenge_summary=WeeklyReportChallengeSummaryResponse(**report.challenge_summary),
            report_text=report.report_text,
            provider=report.provider,
            model_name=report.model_name,
            generated=generated,
            created_at=report.created_at,
            source_type="LLM" if report.provider == OPENAI_PROVIDER else "RULE_BASED",
        )

    @staticmethod
    def _to_list_item(report: WeeklyReport) -> WeeklyReportListItemResponse:
        return WeeklyReportListItemResponse(
            report_id=report.id,
            week_start_date=report.week_start_date,
            week_end_date=report.week_end_date,
            summary_text=WeeklyReportService._summary_text(report.report_text),
            overall_status=WeeklyReportService._overall_status(report.summary_cards),
            created_at=report.created_at,
        )

    @staticmethod
    def _summary_text(report_text: str, max_length: int = 80) -> str:
        if len(report_text) <= max_length:
            return report_text
        return report_text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _limit_text(text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _overall_status(summary_cards: list[dict[str, str]]) -> str:
        statuses = [card.get("status", "UNAVAILABLE") for card in summary_cards]
        if "HIGH" in statuses:
            return "HIGH"
        if "CAUTION" in statuses:
            return "CAUTION"
        if "NORMAL" in statuses:
            return "NORMAL"
        return "UNAVAILABLE"
