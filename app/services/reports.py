import base64
import csv
import html
import io
import json
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status

from app.core import config, default_logger
from app.dtos.reports import (
    CurrentWeeklyReportResponse,
    WeeklyReportChallengeSummaryResponse,
    WeeklyReportExportResponse,
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
from app.services.email import EmailService
from app.services.llm_advice import OPENAI_PROVIDER
from app.services.llm_report import OpenAIReportClient, ReportLLMError, ReportLLMResult
from app.services.notifications import NotificationService

RULE_BASED_PROVIDER = "RULE_BASED"
RULE_BASED_MODEL = "weekly-report-rules-v1"
MAX_REPORT_TEXT_LENGTH = 600
REPORT_DISCLAIMER = "본 리포트는 의료 진단이 아닌 생활습관 점검용 참고 자료입니다."


class WeeklyReportService:
    async def generate_current_week(self, user: User, data: WeeklyReportGenerateRequest) -> WeeklyReportResponse:
        week_start, week_end = self._week_range()
        existing = await WeeklyReport.get_or_none(user_id=user.id, week_start_date=week_start)
        if existing and not data.force_regenerate:
            await self._refresh_report_if_source_changed(existing, user.id)
            return self._to_response(existing, generated=False)
        if existing and data.force_regenerate:
            await existing.delete()

        source_summary = await self._build_source_summary(user.id, week_start, week_end)
        llm_result = await self._generate_llm_report(source_summary)
        report_text = llm_result.report_text if llm_result else self._build_report_text(source_summary)
        previous_report = await self._get_previous_report(user.id, week_start)
        previous_source_summary = await self._build_previous_source_summary(user.id, week_start)
        report = await WeeklyReport.create(
            user=user,
            week_start_date=week_start,
            week_end_date=week_end,
            status="AVAILABLE",
            source_summary=source_summary,
            summary_cards=self._build_summary_cards(source_summary),
            metric_summaries=self._build_metric_summaries(source_summary),
            trend_summary=self._build_trend_summary(previous_report, previous_source_summary),
            challenge_summary=self._build_challenge_summary(source_summary),
            report_text=report_text,
            provider=llm_result.provider if llm_result else RULE_BASED_PROVIDER,
            model_name=llm_result.model_name if llm_result else RULE_BASED_MODEL,
            input_tokens=llm_result.input_tokens if llm_result else 0,
            output_tokens=llm_result.output_tokens if llm_result else 0,
            cache_read_tokens=llm_result.cache_read_tokens if llm_result else 0,
        )
        await NotificationService().notify_weekly_report_created(user_id=user.id, report_id=report.id)
        return self._to_response(report, generated=True)

    async def get_current_week(self, user: User) -> CurrentWeeklyReportResponse:
        week_start, week_end = self._week_range()
        report = await WeeklyReport.get_or_none(user_id=user.id, week_start_date=week_start)
        if report:
            await self._refresh_report_if_source_changed(report, user.id)
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
        await self._refresh_report_if_source_changed(report, user.id)
        return self._to_response(report, generated=False)

    async def get_reports(self, user: User, limit: int = 20) -> list[WeeklyReportListItemResponse]:
        reports = await WeeklyReport.filter(user_id=user.id).order_by("-week_start_date").limit(limit)
        for report in reports:
            await self._refresh_report_if_source_changed(report, user.id)
        return [self._to_list_item(report) for report in reports]

    async def export_report(
        self,
        user: User,
        report_id: int,
        export_format: str,
        send_email: bool = False,
    ) -> WeeklyReportExportResponse:
        report = await WeeklyReport.get_or_none(id=report_id, user_id=user.id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주간 리포트를 찾을 수 없습니다.")
        await self._refresh_report_if_source_changed(report, user.id)

        normalized_format = export_format.upper()
        content_encoding = "TEXT"
        if normalized_format == "CSV":
            content = self._to_csv_content(report)
            content_type = "text/csv;charset=utf-8"
            extension = "csv"
        elif normalized_format == "JSON":
            content = json.dumps(self._export_payload(report), ensure_ascii=False, indent=2, default=str)
            content_type = "application/json;charset=utf-8"
            extension = "json"
        elif normalized_format == "PDF":
            content = base64.b64encode(self._to_pdf_content(report)).decode("ascii")
            content_type = "application/pdf"
            content_encoding = "BASE64"
            extension = "pdf"
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="지원하지 않는 내보내기 형식입니다."
            )

        file_name = f"All4Health_주간리포트_{self._report_created_date(report)}.{extension}"
        emailed = False
        if send_email:
            await EmailService().send_report_export(user.email, file_name, content, content_type, content_encoding)
            emailed = True

        return WeeklyReportExportResponse(
            report_id=report.id,
            file_name=file_name,
            content_type=content_type,
            content=content,
            content_encoding=content_encoding,
            emailed=emailed,
        )

    @staticmethod
    def _report_created_date(report: WeeklyReport) -> date:
        created_at = getattr(report, "created_at", None)
        if isinstance(created_at, datetime):
            return created_at.date()
        if isinstance(created_at, date):
            return created_at
        return report.week_end_date

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
                1 for prediction in predictions if WeeklyReportService._has_risk_signal(prediction)
            ),
            "challenge_checkin_count": challenge_checkin_count,
        }

    @staticmethod
    def _has_risk_signal(prediction: PredictionResult) -> bool:
        if prediction.overall_risk_level in {"MEDIUM", "HIGH"}:
            return True
        return any(item.is_at_risk or item.risk_level in {"MEDIUM", "HIGH"} for item in prediction.items)

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
            report_text=WeeklyReportService._finalize_llm_report(result.report_text),
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
    def _build_trend_summary(
        previous_report: WeeklyReport | None,
        previous_source_summary: dict[str, int] | None = None,
    ) -> dict[str, str | int | None]:
        previous_report_id = previous_report.id if previous_report else None
        previous_summary = previous_report.source_summary if previous_report else previous_source_summary
        if not previous_summary or not WeeklyReportService._has_report_source_data(previous_summary):
            return {
                "status": "UNAVAILABLE",
                "message": "전주 건강 기록이 없어 추이 비교는 제공하지 않습니다.",
                "previous_week_report_id": None,
            }
        previous_records = WeeklyReportService._total_trend_records(previous_summary)
        return {
            "status": "UNCHANGED",
            "message": f"전주 건강 기록 {previous_records}건을 기준으로 이번 주 추이를 비교할 수 있습니다.",
            "previous_week_report_id": previous_report_id,
        }

    @staticmethod
    def _total_trend_records(source_summary: dict[str, int]) -> int:
        return (
            WeeklyReportService._total_health_records(source_summary)
            + source_summary.get("activity_log_count", 0)
            + source_summary.get("exercise_log_count", 0)
            + source_summary.get("meal_log_count", 0)
            + source_summary.get("prediction_count", 0)
            + source_summary.get("challenge_checkin_count", 0)
        )

    @staticmethod
    async def _build_previous_source_summary(user_id: int, week_start: date) -> dict[str, int]:
        previous_week_start = week_start - timedelta(days=7)
        previous_week_end = previous_week_start + timedelta(days=6)
        return await WeeklyReportService._build_source_summary(user_id, previous_week_start, previous_week_end)

    @staticmethod
    async def _get_previous_report(user_id: int, week_start: date) -> WeeklyReport | None:
        previous_week_start = week_start - timedelta(days=7)
        exact_previous = await WeeklyReport.get_or_none(user_id=user_id, week_start_date=previous_week_start)
        if exact_previous:
            return exact_previous
        return (
            await WeeklyReport.filter(user_id=user_id, week_start_date__lt=week_start)
            .order_by("-week_start_date")
            .first()
        )

    async def _refresh_trend_summary_if_needed(self, report: WeeklyReport, user_id: int) -> None:
        trend_summary = report.trend_summary or {}
        if trend_summary.get("previous_week_report_id"):
            return
        previous_report = await self._get_previous_report(user_id, report.week_start_date)
        previous_source_summary = await self._build_previous_source_summary(user_id, report.week_start_date)
        if previous_report is None:
            if not self._has_report_source_data(previous_source_summary):
                return
        report.trend_summary = self._build_trend_summary(previous_report, previous_source_summary)
        await report.save(update_fields=["trend_summary"])

    async def _refresh_report_if_source_changed(self, report: WeeklyReport, user_id: int) -> None:
        source_summary = await self._build_source_summary(user_id, report.week_start_date, report.week_end_date)
        previous_report = await self._get_previous_report(user_id, report.week_start_date)
        previous_source_summary = await self._build_previous_source_summary(user_id, report.week_start_date)
        trend_summary = self._build_trend_summary(previous_report, previous_source_summary)
        source_changed = source_summary != (report.source_summary or {})
        trend_changed = trend_summary != (report.trend_summary or {})
        if not source_changed and not trend_changed:
            return

        report.source_summary = source_summary
        report.summary_cards = self._build_summary_cards(source_summary)
        report.metric_summaries = self._build_metric_summaries(source_summary)
        report.trend_summary = trend_summary
        report.challenge_summary = self._build_challenge_summary(source_summary)
        if source_changed:
            report.report_text = self._build_report_text(source_summary)
            report.provider = RULE_BASED_PROVIDER
            report.model_name = RULE_BASED_MODEL
            report.input_tokens = 0
            report.output_tokens = 0
            report.cache_read_tokens = 0
        await report.save(
            update_fields=[
                "source_summary",
                "summary_cards",
                "metric_summaries",
                "trend_summary",
                "challenge_summary",
                "report_text",
                "provider",
                "model_name",
                "input_tokens",
                "output_tokens",
                "cache_read_tokens",
            ]
        )

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
    def _export_payload(report: WeeklyReport) -> dict:
        return {
            "report_id": report.id,
            "week_start_date": report.week_start_date,
            "week_end_date": report.week_end_date,
            "status": report.status,
            "report_text": report.report_text,
            "source_summary": report.source_summary,
            "summary_cards": report.summary_cards,
            "metric_summaries": report.metric_summaries,
            "trend_summary": report.trend_summary,
            "challenge_summary": report.challenge_summary,
            "provider": report.provider,
            "model_name": report.model_name,
            "created_at": report.created_at,
        }

    @staticmethod
    def _to_csv_content(report: WeeklyReport) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["항목", "값"])
        writer.writerow(["리포트 ID", report.id])
        writer.writerow(["기간", f"{report.week_start_date} ~ {report.week_end_date}"])
        writer.writerow(["상태", report.status])
        writer.writerow(["생성 방식", report.provider])
        writer.writerow(["모델", report.model_name])
        writer.writerow(["리포트 본문", report.report_text])
        writer.writerow([])
        writer.writerow(["요약 카드", "값", "상태", "설명"])
        for card in report.summary_cards:
            writer.writerow([card.get("label"), card.get("value"), card.get("status"), card.get("description")])
        writer.writerow([])
        writer.writerow(["지표", "값", "단위", "상태", "설명"])
        for metric in report.metric_summaries:
            writer.writerow(
                [
                    metric.get("label"),
                    metric.get("value"),
                    metric.get("unit"),
                    metric.get("status"),
                    metric.get("description"),
                ]
            )
        return buffer.getvalue()

    @staticmethod
    def _to_printable_report_html(report: WeeklyReport) -> str:
        def esc(value: object) -> str:
            return html.escape("" if value is None else str(value))
 
        def status_label(status_value: str | None) -> str:
            return {
                "NORMAL": "정상",
                "CAUTION": "주의",
                "HIGH": "위험",
                "UNAVAILABLE": "데이터 부족",
                "ACHIEVED": "달성",
                "IN_PROGRESS": "진행 중",
            }.get(status_value or "", status_value or "확인 필요")
 
        def status_badge_class(status_value: str | None) -> str:
            return {
                "NORMAL": "badge--normal",
                "CAUTION": "badge--caution",
                "HIGH": "badge--high",
                "UNAVAILABLE": "badge--unavail",
                "ACHIEVED": "badge--normal",
                "IN_PROGRESS": "badge--caution",
            }.get(status_value or "", "badge--unavail")
 
        source = report.source_summary or {}
        summary_cards = report.summary_cards or []
        metric_summaries = report.metric_summaries or []
        challenge = report.challenge_summary or {}
        trend = report.trend_summary or {}
 
        total_health_records = WeeklyReportService._total_health_records(source)
        score = min(
            100,
            55
            + min(total_health_records, 5) * 5
            + min(source.get("exercise_log_count", 0), 5) * 3
            + min(source.get("meal_log_count", 0), 5) * 2
            + min(source.get("challenge_checkin_count", 0), 7) * 2,
        )
        completion_rate = int(float(challenge.get("completion_rate") or 0))
 
        # 요약 카드 HTML
        card_icons = ["🩺", "⚠️", "🥗", "🏃", "🏅"]
        card_html_parts = []
        for i, card in enumerate(summary_cards[:5]):
            s = card.get("status", "UNAVAILABLE")
            card_html_parts.append(f"""
        <div class="card">
          <span class="card__icon">{card_icons[i % len(card_icons)]}</span>
          <p class="card__label">{esc(card.get("label"))}</p>
          <p class="card__value">{esc(card.get("value"))}</p>
          <span class="badge {status_badge_class(s)}">{esc(status_label(s))}</span>
        </div>""")
 
        # 지표 바 HTML
        bar_html_parts = []
        for metric in metric_summaries:
            raw = int("".join(ch for ch in str(metric.get("value", "0")) if ch.isdigit()) or "0")
            pct = min(100, max(4, raw * 12))
            bar_html_parts.append(f"""
        <div class="bar-row">
          <span class="bar-row__label">{esc(metric.get("label"))}</span>
          <span class="bar-row__val">{esc(metric.get("value"))}{esc(metric.get("unit") or "")}</span>
          <div class="bar-row__track"><div class="bar-row__fill" style="width:{pct}%"></div></div>
        </div>""")
 
        # 목표 달성 HTML
        goal_rows = [
            ("혈압·혈당", source.get("vital_record_count", 0), "주 3회 이상"),
            ("식단 기록",  source.get("meal_log_count", 0),    "주 5회"),
            ("운동 기록",  source.get("exercise_log_count", 0), "주 3회"),
            ("챌린지",    source.get("challenge_checkin_count", 0), "주 3회 이상"),
        ]
        goal_html_parts = []
        for lbl, count, target in goal_rows:
            icon = "✓" if count else "○"
            cls = "goal--done" if count else "goal--todo"
            goal_html_parts.append(
                f'<li class="goal-item {cls}"><span class="goal-item__icon">{icon}</span>'
                f'<span class="goal-item__lbl">{esc(lbl)}</span>'
                f'<span class="goal-item__count">{count}회</span>'
                f'<span class="goal-item__target">목표 {esc(target)}</span></li>'
            )
 
        # 상세 테이블 HTML
        table_rows = []
        for metric in metric_summaries:
            s = metric.get("status", "UNAVAILABLE")
            table_rows.append(f"""
        <tr>
          <td>{esc(metric.get("label"))}</td>
          <td>{esc(metric.get("value"))}{esc(metric.get("unit") or "")}</td>
          <td><span class="badge {status_badge_class(s)}">{esc(status_label(s))}</span></td>
          <td class="td--desc">{esc(metric.get("description"))}</td>
        </tr>""")
 
        challenge_msg = esc(challenge.get("message", "이번 주 생활습관 실천 내용을 확인했습니다."))
        trend_msg     = esc(trend.get("message", "다음 리포트에서 추이를 비교할 수 있습니다."))
 
        return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>All4Health 주간 리포트</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
 
    :root {{
      --green:      #2D7A4F;
      --green-lt:   #EAF4EE;
      --green-md:   #A8D5B5;
      --red:        #D94F4F;
      --red-lt:     #FDF0F0;
      --orange:     #E07A2B;
      --orange-lt:  #FEF4EB;
      --gray-50:    #F8F9FA;
      --gray-100:   #F1F3F5;
      --gray-200:   #E9ECEF;
      --gray-400:   #ADB5BD;
      --gray-600:   #6C757D;
      --gray-800:   #343A40;
      --gray-900:   #212529;
      --radius-sm:  6px;
      --radius-md:  10px;
      --radius-lg:  14px;
      --shadow-sm:  0 1px 4px rgba(0,0,0,.06);
      --shadow-md:  0 4px 16px rgba(0,0,0,.08);
    }}
 
    body {{
      background: var(--gray-50);
      color: var(--gray-900);
      font-family: "Noto Sans KR", -apple-system, "Apple SD Gothic Neo", sans-serif;
      font-size: 14px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}
 
    /* ── 레이아웃 ── */
    .page {{
      max-width: 780px;
      margin: 32px auto 64px;
      padding: 0 16px;
    }}
 
    /* ── 헤더 ── */
    .header {{
      background: var(--green);
      border-radius: var(--radius-lg);
      padding: 36px 40px;
      color: #fff;
      margin-bottom: 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }}
    .header__brand {{ font-size: 22px; font-weight: 700; letter-spacing: -0.03em; margin-bottom: 4px; }}
    .header__sub   {{ font-size: 13px; color: var(--green-md); }}
    .header__period{{ font-size: 13px; color: var(--green-md); margin-top: 2px; }}
    .score-badge {{
      text-align: center;
      background: rgba(255,255,255,.12);
      border-radius: var(--radius-md);
      padding: 16px 28px;
      min-width: 108px;
      flex-shrink: 0;
    }}
    .score-badge__num  {{ font-size: 36px; font-weight: 700; line-height: 1; }}
    .score-badge__unit {{ font-size: 12px; color: var(--green-md); margin-top: 4px; }}
 
    /* ── 섹션 ── */
    .section {{ margin-bottom: 28px; }}
    .section__title {{
      font-size: 13px;
      font-weight: 600;
      color: var(--gray-600);
      text-transform: uppercase;
      letter-spacing: .06em;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .section__title::after {{
      content: "";
      flex: 1;
      height: 1px;
      background: var(--gray-200);
    }}
 
    /* ── 요약 카드 ── */
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
      gap: 12px;
    }}
    .card {{
      background: #fff;
      border: 1px solid var(--gray-200);
      border-radius: var(--radius-md);
      padding: 18px 16px 14px;
      box-shadow: var(--shadow-sm);
    }}
    .card__icon  {{ font-size: 20px; display: block; margin-bottom: 10px; }}
    .card__label {{ font-size: 11px; color: var(--gray-600); font-weight: 500; margin-bottom: 4px; }}
    .card__value {{ font-size: 22px; font-weight: 700; color: var(--gray-900); margin-bottom: 8px; line-height: 1.2; }}
 
    /* ── 배지 ── */
    .badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 600;
      border-radius: 999px;
      padding: 2px 10px;
    }}
    .badge--normal  {{ background: var(--green-lt);  color: var(--green); }}
    .badge--caution {{ background: var(--orange-lt); color: var(--orange); }}
    .badge--high    {{ background: var(--red-lt);    color: var(--red); }}
    .badge--unavail {{ background: var(--gray-100);  color: var(--gray-400); }}
 
    /* ── AI 요약 박스 ── */
    .summary-box {{
      background: #fff;
      border: 1px solid var(--gray-200);
      border-left: 4px solid var(--green);
      border-radius: var(--radius-md);
      padding: 20px 22px;
      font-size: 14px;
      line-height: 1.75;
      color: var(--gray-800);
      box-shadow: var(--shadow-sm);
      white-space: pre-wrap;
    }}
 
    /* ── 바 차트 ── */
    .bars {{ display: flex; flex-direction: column; gap: 14px; }}
    .bar-row {{ display: grid; grid-template-columns: 88px 44px 1fr; align-items: center; gap: 12px; }}
    .bar-row__label {{ font-size: 13px; color: var(--gray-600); }}
    .bar-row__val   {{ font-size: 13px; font-weight: 600; text-align: right; color: var(--gray-800); }}
    .bar-row__track {{ height: 6px; background: var(--gray-100); border-radius: 999px; overflow: hidden; }}
    .bar-row__fill  {{ height: 100%; background: var(--green); border-radius: 999px; transition: width .4s; }}
 
    /* ── 목표 달성 ── */
    .progress-ring-wrap {{
      display: flex;
      align-items: center;
      gap: 28px;
      margin-bottom: 20px;
    }}
    .progress-ring-label {{ font-size: 32px; font-weight: 700; color: var(--green); }}
    .progress-ring-sub   {{ font-size: 13px; color: var(--gray-600); margin-top: 2px; }}
    .goal-list {{ list-style: none; display: flex; flex-direction: column; gap: 8px; }}
    .goal-item {{
      display: grid;
      grid-template-columns: 20px 1fr auto auto;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      padding: 10px 14px;
      border-radius: var(--radius-sm);
      background: #fff;
      border: 1px solid var(--gray-200);
    }}
    .goal--done {{ border-color: var(--green-md); }}
    .goal-item__icon   {{ font-size: 14px; font-weight: 700; color: var(--green); }}
    .goal--todo .goal-item__icon {{ color: var(--gray-400); }}
    .goal-item__lbl    {{ font-weight: 500; }}
    .goal-item__count  {{ font-weight: 700; color: var(--gray-800); }}
    .goal-item__target {{ font-size: 11px; color: var(--gray-400); }}
 
    /* ── 상세 테이블 ── */
    .detail-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .detail-table th {{
      background: var(--gray-100);
      padding: 10px 14px;
      text-align: left;
      font-weight: 600;
      color: var(--gray-600);
      font-size: 12px;
    }}
    .detail-table td {{ padding: 11px 14px; border-bottom: 1px solid var(--gray-100); color: var(--gray-800); }}
    .detail-table tr:last-child td {{ border-bottom: none; }}
    .td--desc {{ color: var(--gray-400); font-size: 12px; }}
    .table-wrap {{ background: #fff; border: 1px solid var(--gray-200); border-radius: var(--radius-md); overflow: hidden; box-shadow: var(--shadow-sm); }}
 
    /* ── 조언 박스 ── */
    .advice-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .advice-box {{
      padding: 20px;
      border-radius: var(--radius-md);
      border: 1px solid transparent;
    }}
    .advice-box--caution {{ background: var(--red-lt); border-color: #f7c5c5; }}
    .advice-box--good    {{ background: var(--green-lt); border-color: var(--green-md); }}
    .advice-box__title {{ font-size: 12px; font-weight: 700; margin-bottom: 8px; }}
    .advice-box--caution .advice-box__title {{ color: var(--red); }}
    .advice-box--good    .advice-box__title {{ color: var(--green); }}
    .advice-box__body {{ font-size: 13px; line-height: 1.65; color: var(--gray-700); }}
 
    /* ── 다음 단계 ── */
    .next-steps {{ list-style: none; display: flex; flex-direction: column; gap: 10px; }}
    .next-steps li {{
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 18px;
      background: #fff;
      border: 1px solid var(--gray-200);
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 500;
      color: var(--gray-800);
      box-shadow: var(--shadow-sm);
    }}
    .step-num {{
      width: 26px; height: 26px;
      background: var(--green);
      color: #fff;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 700;
      flex-shrink: 0;
    }}
 
    /* ── 면책 고지 ── */
    .disclaimer {{
      text-align: center;
      font-size: 11px;
      color: var(--gray-400);
      margin-top: 32px;
      padding-top: 20px;
      border-top: 1px solid var(--gray-200);
    }}
 
    /* ── 인쇄 ── */
    @media print {{
      body {{ background: #fff; }}
      .page {{ margin: 0; max-width: none; padding: 0; }}
      .header {{ border-radius: 0; }}
    }}
  </style>
</head>
<body>
  <main class="page">
 
    <!-- ── 헤더 ── -->
    <header class="header">
      <div>
        <p class="header__brand">All4Health</p>
        <p class="header__sub">주간 건강 리포트</p>
        <p class="header__period">{esc(report.week_start_date)} – {esc(report.week_end_date)}</p>
      </div>
      <div class="score-badge">
        <p class="score-badge__num">{score}</p>
        <p class="score-badge__unit">종합 점수</p>
      </div>
    </header>
 
    <!-- ── 요약 카드 ── -->
    <section class="section">
      <h2 class="section__title">이번 주 요약</h2>
      <div class="cards">{"".join(card_html_parts)}</div>
    </section>
 
    <!-- ── AI 요약 ── -->
    <section class="section">
      <h2 class="section__title">AI 분석 요약</h2>
      <div class="summary-box">{esc(report.report_text)}</div>
    </section>
 
    <!-- ── 관리 영역별 성과 ── -->
    <section class="section">
      <h2 class="section__title">관리 영역별 성과</h2>
      <div class="bars">{"".join(bar_html_parts)}</div>
    </section>
 
    <!-- ── 목표 달성률 ── -->
    <section class="section">
      <h2 class="section__title">목표 달성률</h2>
      <div class="progress-ring-wrap">
        <div>
          <p class="progress-ring-label">{completion_rate}%</p>
          <p class="progress-ring-sub">이번 주 챌린지 달성</p>
        </div>
      </div>
      <ul class="goal-list">{"".join(goal_html_parts)}</ul>
    </section>
 
    <!-- ── 상세 분석 ── -->
    <section class="section">
      <h2 class="section__title">상세 분석</h2>
      <div class="table-wrap">
        <table class="detail-table">
          <thead><tr><th>영역</th><th>기록</th><th>상태</th><th>설명</th></tr></thead>
          <tbody>{"".join(table_rows)}</tbody>
        </table>
      </div>
    </section>
 
    <!-- ── 건강 조언 ── -->
    <section class="section">
      <h2 class="section__title">건강 조언</h2>
      <div class="advice-grid">
        <div class="advice-box advice-box--caution">
          <p class="advice-box__title">⚠ 주의할 점</p>
          <p class="advice-box__body">혈압·혈당 수치를 주기적으로 확인하세요. 식단과 운동 기록을 꾸준히 남기면 리포트 정확도가 높아집니다.</p>
        </div>
        <div class="advice-box advice-box--good">
          <p class="advice-box__title">✓ 잘한 점</p>
          <p class="advice-box__body">{challenge_msg} {trend_msg}</p>
        </div>
      </div>
    </section>
 
    <!-- ── 다음 단계 ── -->
    <section class="section">
      <h2 class="section__title">다음 단계</h2>
      <ol class="next-steps">
        <li><span class="step-num">1</span>주 4회 이상 유산소 운동 기록</li>
        <li><span class="step-num">2</span>나트륨 섭취 줄이기</li>
        <li><span class="step-num">3</span>정기적인 혈압·혈당 모니터링</li>
      </ol>
    </section>
 
    <p class="disclaimer">{esc(REPORT_DISCLAIMER)}</p>
 
  </main>
</body>
</html>"""
    
    @staticmethod
    def _to_pdf_content(report: WeeklyReport) -> bytes:  # noqa: C901
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PDF 생성 모듈이 설치되지 않았습니다. 서버 의존성을 다시 설치해주세요.",
            ) from exc
 
        # ── 폰트 등록 ──────────────────────────────────────────────────────────
        # HYSMyeongJo-Medium: 명조 계열 / 본문 가독성 우수
        # HYGothic-Medium:    고딕 계열 / 레이블·수치에 사용
        for font_name in ("HYSMyeongJo-Medium", "HYGothic-Medium"):
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))
 
        FN_BODY  = "HYSMyeongJo-Medium"   # 본문용 (명조)
        FN_UI    = "HYGothic-Medium"       # UI 레이블·수치용 (고딕)
 
        # ── 색상 팔레트 ────────────────────────────────────────────────────────
        C_GREEN   = colors.HexColor("#2D7A4F")
        C_GREEN_D = colors.HexColor("#1F5C3A")
        C_GREEN_L = colors.HexColor("#EAF4EE")
        C_GREEN_M = colors.HexColor("#A8D5B5")
        C_RED     = colors.HexColor("#D94F4F")
        C_RED_L   = colors.HexColor("#FDF0F0")
        C_ORANGE  = colors.HexColor("#E07A2B")
        C_GRAY_50 = colors.HexColor("#F8F9FA")
        C_GRAY_100= colors.HexColor("#F1F3F5")
        C_GRAY_200= colors.HexColor("#E9ECEF")
        C_GRAY_400= colors.HexColor("#ADB5BD")
        C_GRAY_600= colors.HexColor("#6C757D")
        C_GRAY_800= colors.HexColor("#343A40")
        C_GRAY_900= colors.HexColor("#212529")
        C_WHITE   = colors.white
 
        # ── 페이지 기본값 ───────────────────────────────────────────────────────
        buffer = io.BytesIO()
        pw, ph = A4                      # 595 × 842 pt
        MG   = 44                        # 좌우 마진
        CW   = pw - MG * 2              # 콘텐츠 너비
 
        cv = canvas.Canvas(buffer, pagesize=A4)
 
        # ── 헬퍼 ───────────────────────────────────────────────────────────────
        def sf(size: int, font=FN_UI, fill=None) -> None:
            cv.setFont(font, size)
            cv.setFillColor(fill if fill is not None else C_GRAY_900)
 
        def wrap_text(text: str, x: float, y: float, max_w: float,
                      size: int, font=FN_BODY, lead: int = 15, fill=None) -> float:
            sf(size, font, fill)
            for para in (str(text) or "").splitlines() or [""]:
                line = ""
                for word in para.split():
                    cand = word if not line else f"{line} {word}"
                    if pdfmetrics.stringWidth(cand, font, size) <= max_w:
                        line = cand
                    else:
                        cv.drawString(x, y, line)
                        y -= lead
                        line = word
                if line:
                    cv.drawString(x, y, line)
                    y -= lead
            return y
 
        def section_title(title: str, y: float, icon: str = "") -> float:
            sf(9, FN_UI, C_GRAY_600)
            label = f"{icon}  {title}" if icon else title
            cv.drawString(MG, y, label)
            cv.setStrokeColor(C_GRAY_200)
            cv.setLineWidth(0.5)
            cv.line(MG, y - 6, pw - MG, y - 6)
            return y - 22
 
        def chip(x: float, y: float, text: str, bg_col, txt_col, w: float = 52, h: float = 14) -> None:
            cv.setFillColor(bg_col)
            cv.roundRect(x, y - h / 2, w, h, 4, stroke=0, fill=1)
            sf(7, FN_UI, txt_col)
            cv.drawCentredString(x + w / 2, y - h / 2 + 3.5, text)
 
        def footer_page(page: int, total: int = 2) -> None:
            cv.setStrokeColor(C_GRAY_200)
            cv.setLineWidth(0.4)
            cv.line(MG, 34, pw - MG, 34)
            sf(7, FN_UI, C_GRAY_400)
            cv.drawString(MG, 22, "All4Health © 2026")
            cv.drawCentredString(pw / 2, 22, REPORT_DISCLAIMER)
            cv.drawRightString(pw - MG, 22, f"{page} / {total}")
 
        def status_chip(x: float, y: float, status_val: str | None) -> None:
            label_map  = {"NORMAL": "정상", "CAUTION": "주의", "HIGH": "위험", "UNAVAILABLE": "데이터 부족",
                          "ACHIEVED": "달성", "IN_PROGRESS": "진행 중"}
            bg_map     = {"NORMAL": C_GREEN_L, "CAUTION": colors.HexColor("#FEF4EB"),
                          "HIGH": C_RED_L,     "UNAVAILABLE": C_GRAY_100,
                          "ACHIEVED": C_GREEN_L, "IN_PROGRESS": colors.HexColor("#FEF4EB")}
            txt_map    = {"NORMAL": C_GREEN,   "CAUTION": C_ORANGE,
                          "HIGH": C_RED,       "UNAVAILABLE": C_GRAY_400,
                          "ACHIEVED": C_GREEN,  "IN_PROGRESS": C_ORANGE}
            sv = status_val or "UNAVAILABLE"
            chip(x, y, label_map.get(sv, sv), bg_map.get(sv, C_GRAY_100), txt_map.get(sv, C_GRAY_400))
 
        # ── 데이터 추출 ────────────────────────────────────────────────────────
        source    = getattr(report, "source_summary",   None) or {}
        challenge = getattr(report, "challenge_summary", None) or {}
        trend     = getattr(report, "trend_summary",    None) or {}
        total_hr  = WeeklyReportService._total_health_records(source)
        score     = min(
            100,
            55
            + min(total_hr, 5) * 5
            + min(source.get("exercise_log_count", 0), 5) * 3
            + min(source.get("meal_log_count", 0), 5) * 2
            + min(source.get("challenge_checkin_count", 0), 7) * 2,
        )
        completion_rate = int(float(challenge.get("completion_rate") or 0))
 
        # ══════════════════════════════════════════════════════════════════════
        #  PAGE 1
        # ══════════════════════════════════════════════════════════════════════
        HDR_H = 110
 
        # 헤더 배경
        cv.setFillColor(C_GREEN)
        cv.rect(0, ph - HDR_H, pw, HDR_H, stroke=0, fill=1)
 
        # 브랜드명
        sf(18, FN_UI, C_WHITE)
        cv.drawString(MG, ph - 36, "All4Health")
        sf(9, FN_UI, C_GREEN_M)
        cv.drawString(MG, ph - 52, "주간 건강 리포트")
        sf(8, FN_UI, colors.HexColor("#C8E6CE"))
        cv.drawString(MG, ph - 66, f"{report.week_start_date}  –  {report.week_end_date}")
 
        # 점수 박스
        sx, sy = pw - MG - 80, ph - HDR_H + 12
        cv.setFillColor(C_GREEN_D)
        cv.roundRect(sx, sy, 80, 86, 8, stroke=0, fill=1)
        sf(7.5, FN_UI, C_GREEN_M)
        cv.drawCentredString(sx + 40, sy + 70, "종합 점수")
        sf(28, FN_UI, C_WHITE)
        cv.drawCentredString(sx + 40, sy + 34, str(score))
        sf(8, FN_UI, C_GREEN_M)
        cv.drawCentredString(sx + 40, sy + 16, "점")
 
        y = ph - HDR_H - 26
 
        # ── 요약 카드 (2×2 그리드) ─────────────────────────────────────────────
        cards_data = (report.summary_cards or [])[:4]
        card_labels = [d.get("label", "") for d in cards_data]
        card_values = [str(d.get("value", "")) for d in cards_data]
        card_statuses = [d.get("status") for d in cards_data]
        if not cards_data:
            card_labels  = ["건강 기록", "AI 위험 신호", "식단 기록", "운동 기록"]
            card_values  = [f"{total_hr}건", "—",
                            f"{source.get('meal_log_count',0)}건",
                            f"{source.get('exercise_log_count',0)}건"]
            card_statuses = ["NORMAL", "NORMAL", "NORMAL", "NORMAL"]
 
        ACCENT = [C_GREEN, C_RED, colors.HexColor("#14A85B"), colors.HexColor("#7B1FA2")]
        cw = (CW - 10) / 2
        ch = 58
        for i in range(min(4, len(card_labels))):
            cx_ = MG + (i % 2) * (cw + 10)
            cy_ = y - (i // 2) * (ch + 10)
            cv.setFillColor(C_GRAY_50)
            cv.roundRect(cx_, cy_ - ch, cw, ch, 6, stroke=0, fill=1)
            # 왼쪽 액센트 바
            cv.setFillColor(ACCENT[i % len(ACCENT)])
            cv.roundRect(cx_, cy_ - ch, 3, ch, 2, stroke=0, fill=1)
            sf(7.5, FN_UI, C_GRAY_600)
            cv.drawString(cx_ + 12, cy_ - 16, card_labels[i])
            sf(18, FN_UI, ACCENT[i % len(ACCENT)])
            cv.drawString(cx_ + 12, cy_ - 38, card_values[i])
            status_chip(cx_ + cw - 58, cy_ - 28, card_statuses[i])
 
        y -= ch * 2 + 10 * 2 + 22
 
        # ── AI 분석 요약 ────────────────────────────────────────────────────────
        y = section_title("AI 분석 요약", y, "✦")
        BOX_H = 80
        cv.setFillColor(C_GRAY_50)
        cv.roundRect(MG, y - BOX_H, CW, BOX_H, 6, stroke=0, fill=1)
        cv.setFillColor(C_GREEN)
        cv.roundRect(MG, y - BOX_H, 3, BOX_H, 2, stroke=0, fill=1)
        wrap_text(report.report_text or "분석 내용 없음",
                  MG + 14, y - 14, CW - 24, 8.5, FN_BODY, 13)
        y -= BOX_H + 22
 
        # ── 관리 영역별 성과 ────────────────────────────────────────────────────
        y = section_title("관리 영역별 성과", y, "◈")
        bar_x = MG + 92
        bar_w = CW - 92 - 4
        for metric in (report.metric_summaries or [])[:5]:
            lbl  = str(metric.get("label", ""))
            val_s = str(metric.get("value", "0"))
            unit  = metric.get("unit") or ""
            raw   = int("".join(ch for ch in val_s if ch.isdigit()) or "0")
            # 레이블
            sf(8.5, FN_UI, C_GRAY_600)
            cv.drawString(MG, y, lbl)
            # 수치
            sf(8.5, FN_UI, C_GRAY_800)
            cv.drawRightString(bar_x - 6, y, f"{val_s}{unit}")
            # 트랙
            cv.setFillColor(C_GRAY_200)
            cv.roundRect(bar_x, y - 2, bar_w, 6, 3, stroke=0, fill=1)
            fill_w = min(bar_w, max(10, raw * 14))
            cv.setFillColor(C_GREEN)
            cv.roundRect(bar_x, y - 2, fill_w, 6, 3, stroke=0, fill=1)
            y -= 20
 
        footer_page(1)
        cv.showPage()
 
        # ══════════════════════════════════════════════════════════════════════
        #  PAGE 2
        # ══════════════════════════════════════════════════════════════════════
        y = ph - 56
 
        # ── 목표 달성률 ─────────────────────────────────────────────────────────
        y = section_title("목표 달성률", y, "◎")
        sf(28, FN_UI, C_GREEN)
        cv.drawString(MG, y, f"{completion_rate}%")
        sf(9, FN_UI, C_GRAY_600)
        cv.drawString(MG + 56, y, "달성")
        y -= 26
 
        for lbl, count, target in [
            ("혈압·혈당", source.get("vital_record_count", 0),    "주 3회 이상"),
            ("식단 기록",  source.get("meal_log_count", 0),         "주 5회"),
            ("운동 기록",  source.get("exercise_log_count", 0),     "주 3회"),
            ("챌린지",    source.get("challenge_checkin_count", 0), "주 3회 이상"),
        ]:
            done = bool(count)
            cv.setFillColor(C_GRAY_50)
            cv.roundRect(MG, y - 18, CW, 22, 4, stroke=0, fill=1)
            if done:
                cv.setFillColor(C_GREEN)
                cv.roundRect(MG, y - 18, 3, 22, 2, stroke=0, fill=1)
            sf(8.5, FN_UI, C_GREEN if done else C_GRAY_400)
            cv.drawString(MG + 10, y - 10, "✓" if done else "○")
            sf(8.5, FN_BODY, C_GRAY_800)
            cv.drawString(MG + 26, y - 10, f"{lbl}: {count}회")
            tw = pdfmetrics.stringWidth(f"{lbl}: {count}회", FN_BODY, 8.5)
            sf(7.5, FN_UI, C_GRAY_400)
            cv.drawString(MG + 26 + tw + 8, y - 10, f"목표 {target}")
            y -= 26
        y -= 14
 
        # ── 상세 분석 ───────────────────────────────────────────────────────────
        y = section_title("상세 분석", y, "≡")
        col_x = [MG, MG + 100, MG + 168, MG + 230, MG + 340]
        ROW_H = 22
 
        # 헤더 행
        cv.setFillColor(C_GREEN)
        cv.roundRect(MG, y - ROW_H, CW, ROW_H + 2, 4, stroke=0, fill=1)
        sf(8, FN_UI, C_WHITE)
        for xi, h in zip(col_x, ["영역", "기록", "상태", "설명"]):
            cv.drawString(xi + 6, y - 14, h)
        y -= ROW_H + 4
 
        for idx, metric in enumerate((report.metric_summaries or [])[:7]):
            bg = C_GRAY_50 if idx % 2 == 0 else C_WHITE
            cv.setFillColor(bg)
            cv.rect(MG, y - ROW_H, CW, ROW_H, stroke=0, fill=1)
            sf(8, FN_BODY, C_GRAY_800)
            cv.drawString(col_x[0] + 6, y - 14, str(metric.get("label", "")))
            cv.drawString(col_x[1] + 6, y - 14, f"{metric.get('value','')}{metric.get('unit') or ''}")
            status_chip(col_x[2] + 6, y - 7, metric.get("status"))
            sf(7.5, FN_BODY, C_GRAY_400)
            cv.drawString(col_x[3] + 6, y - 14, str(metric.get("description", ""))[:40])
            cv.setStrokeColor(C_GRAY_200)
            cv.setLineWidth(0.3)
            cv.line(MG, y - ROW_H, pw - MG, y - ROW_H)
            y -= ROW_H
        y -= 18
 
        # ── 건강 조언 ───────────────────────────────────────────────────────────
        y = section_title("건강 조언", y, "♡")
        half_w = (CW - 10) / 2
 
        def advice_rect(ax: float, ay: float, aw: float, title: str,
                        body: str, bg_col, accent_col, title_col) -> float:
            abox_h = 70
            cv.setFillColor(bg_col)
            cv.roundRect(ax, ay - abox_h, aw, abox_h, 6, stroke=0, fill=1)
            cv.setFillColor(accent_col)
            cv.roundRect(ax, ay - abox_h, 3, abox_h, 2, stroke=0, fill=1)
            sf(8.5, FN_UI, title_col)
            cv.drawString(ax + 12, ay - 16, title)
            wrap_text(body, ax + 12, ay - 30, aw - 20, 7.5, FN_BODY, 12, C_GRAY_600)
            return ay - abox_h
 
        good_msg = (
            f"{challenge.get('message','이번 주 생활습관 실천 내용을 확인했습니다.')} "
            f"{trend.get('message','다음 리포트에서 추이를 비교할 수 있습니다.')}"
        )
        advice_rect(MG, y, half_w,
                    "⚠ 주의할 점",
                    "혈압·혈당 수치를 주기적으로 확인하세요. 식단과 운동 기록을 꾸준히 남기면 리포트 정확도가 높아집니다.",
                    C_RED_L, C_RED, C_RED)
        advice_rect(MG + half_w + 10, y, half_w,
                    "✓ 잘한 점", good_msg,
                    C_GREEN_L, C_GREEN, C_GREEN)
        y -= 80
 
        # ── 다음 단계 ───────────────────────────────────────────────────────────
        y = section_title("다음 단계", y, "→")
        for step_i, step_text in enumerate(["주 4회 이상 유산소 운동 기록", "나트륨 섭취 줄이기", "정기적인 혈압·혈당 모니터링"]):
            cv.setFillColor(C_GRAY_50)
            cv.roundRect(MG, y - 22, CW, 24, 5, stroke=0, fill=1)
            cv.setFillColor(C_GREEN)
            cv.circle(MG + 14, y - 10, 9, stroke=0, fill=1)
            sf(7.5, FN_UI, C_WHITE)
            cv.drawCentredString(MG + 14, y - 13, str(step_i + 1))
            sf(8.5, FN_BODY, C_GRAY_800)
            cv.drawString(MG + 30, y - 13, step_text)
            y -= 28
        y -= 12
 
        # 면책 고지
        cv.setFillColor(C_GRAY_100)
        cv.roundRect(MG, y - 22, CW, 24, 5, stroke=0, fill=1)
        sf(7.5, FN_UI, C_GRAY_400)
        cv.drawCentredString(pw / 2, y - 13, REPORT_DISCLAIMER)
 
        footer_page(2)
        cv.save()
        return buffer.getvalue()
 
 

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
    def _finalize_llm_report(text: str) -> str:
        normalized = " ".join(text.split())
        has_disclaimer = "의료 진단" in normalized or "참고 자료" in normalized or "생활습관 점검" in normalized
        if not has_disclaimer:
            normalized = f"{normalized} {REPORT_DISCLAIMER}"
        return WeeklyReportService._limit_text(normalized, MAX_REPORT_TEXT_LENGTH)

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
