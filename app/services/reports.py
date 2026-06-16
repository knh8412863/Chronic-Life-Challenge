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
            ("식단 기록", source.get("meal_log_count", 0), "주 5회"),
            ("운동 기록", source.get("exercise_log_count", 0), "주 3회"),
            ("챌린지", source.get("challenge_checkin_count", 0), "주 3회 이상"),
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
        trend_msg = esc(trend.get("message", "다음 리포트에서 추이를 비교할 수 있습니다."))

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
            from pathlib import Path

            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PDF 생성 모듈이 설치되지 않았습니다. 서버 의존성을 다시 설치해주세요.",
            ) from exc

        font_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "nanum"
        font_name = "NanumGothic"
        try:
            pdfmetrics.registerFont(TTFont(font_name, str(font_dir / "NanumGothic.ttf")))
        except Exception:
            font_name = "HYGothic-Medium"
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        page_width, page_height = A4
        margin_x = 42
        top_y = page_height - 42
        content_width = page_width - margin_x * 2

        brand = colors.HexColor("#0E7A5F")
        brand_dark = colors.HexColor("#0A5A46")
        brand_soft = colors.HexColor("#E7F3EF")
        ink = colors.HexColor("#14181B")
        ink_2 = colors.HexColor("#3F474D")
        muted = colors.HexColor("#737D85")
        muted_2 = colors.HexColor("#AAB2B9")
        line = colors.HexColor("#ECEEF0")
        panel = colors.HexColor("#F7F9F8")
        panel_2 = colors.HexColor("#F1F4F3")
        red = colors.HexColor("#E0584C")
        red_soft = colors.HexColor("#FBEDEB")
        orange = colors.HexColor("#DD8A2E")
        orange_soft = colors.HexColor("#FBF2E6")
        violet = colors.HexColor("#6C6CF0")
        warn = colors.HexColor("#E0A82E")
        white = colors.white

        source = getattr(report, "source_summary", None) or {}
        challenge = getattr(report, "challenge_summary", None) or {}
        trend = getattr(report, "trend_summary", None) or {}
        summary_cards = list(getattr(report, "summary_cards", None) or [])
        metric_summaries = list(getattr(report, "metric_summaries", None) or [])
        total_records = WeeklyReportService._total_health_records(source)
        challenge_rate = int(float(challenge.get("completion_rate") or 0))
        score = min(
            100,
            45
            + min(total_records, 5) * 6
            + min(source.get("exercise_log_count", 0), 5) * 3
            + min(source.get("meal_log_count", 0), 5) * 2
            + min(source.get("activity_log_count", 0), 5) * 2
            + min(source.get("challenge_checkin_count", 0), 7) * 2,
        )
        grade = "양호" if score >= 75 else "주의" if score >= 55 else "관리 필요"
        report_no = f"WR-{report.week_end_date.strftime('%Y%m%d')}-{getattr(report, 'id', 0)}"

        if not summary_cards:
            summary_cards = WeeklyReportService._build_summary_cards(source)
        if not metric_summaries:
            metric_summaries = WeeklyReportService._build_metric_summaries(source)

        def set_font(size: float, color=ink) -> None:
            c.setFont(font_name, size)
            c.setFillColor(color)

        def text_width(text: str, size: float) -> float:
            return pdfmetrics.stringWidth(str(text), font_name, size)

        def draw_wrapped(
            text: str, x: float, y: float, max_width: float, size: float, leading: float, color=ink_2
        ) -> float:
            set_font(size, color)
            paragraphs = str(text or "").splitlines() or [""]
            for paragraph in paragraphs:
                line_text = ""
                for word in paragraph.split(" "):
                    candidate = word if not line_text else f"{line_text} {word}"
                    if text_width(candidate, size) <= max_width:
                        line_text = candidate
                    else:
                        if line_text:
                            c.drawString(x, y, line_text)
                            y -= leading
                        line_text = word
                if line_text:
                    c.drawString(x, y, line_text)
                    y -= leading
            return y

        def draw_footer(page: int) -> None:
            c.setStrokeColor(line)
            c.setLineWidth(0.6)
            c.line(margin_x, 34, page_width - margin_x, 34)
            set_font(7.2, muted_2)
            c.drawString(margin_x, 22, "All4Health · Weekly Health Report")
            c.drawCentredString(page_width / 2, 22, REPORT_DISCLAIMER)
            c.drawRightString(page_width - margin_x, 22, f"{page} / 2")

        def draw_section_header(y: float, eyebrow: str, title: str, meta: str = "") -> float:
            set_font(7.5, brand)
            c.drawString(margin_x, y, eyebrow.upper())
            set_font(12.5, ink)
            c.drawString(margin_x + 72, y - 1, title)
            rule_x = margin_x + 72 + text_width(title, 12.5) + 12
            c.setStrokeColor(line)
            c.setLineWidth(0.7)
            c.line(rule_x, y + 2, page_width - margin_x - (text_width(meta, 8.5) + 8 if meta else 0), y + 2)
            if meta:
                set_font(8.5, muted)
                c.drawRightString(page_width - margin_x, y - 1, meta)
            return y - 22

        def draw_round_rect(x: float, y: float, w: float, h: float, fill, stroke=line, radius: float = 12) -> None:
            c.setFillColor(fill)
            c.setStrokeColor(stroke)
            c.setLineWidth(0.7)
            c.roundRect(x, y, w, h, radius, stroke=1, fill=1)

        def draw_pill(x: float, y: float, label: str, status_value: str | None = None) -> None:
            status_value = status_value or "UNAVAILABLE"
            palette = {
                "NORMAL": (brand_soft, brand, "정상"),
                "CAUTION": (orange_soft, orange, "주의"),
                "HIGH": (red_soft, red, "위험"),
                "UNAVAILABLE": (panel_2, muted, "데이터 부족"),
                "ACHIEVED": (brand_soft, brand, "달성"),
                "IN_PROGRESS": (orange_soft, orange, "진행 중"),
            }
            bg, fg, default_label = palette.get(status_value, (panel_2, muted, status_value))
            label = label or default_label
            w = max(46, text_width(label, 7.2) + 16)
            c.setFillColor(bg)
            c.roundRect(x, y, w, 15, 7.5, stroke=0, fill=1)
            set_font(7.2, fg)
            c.drawCentredString(x + w / 2, y + 4.2, label)

        def draw_progress(x: float, y: float, w: float, value: float, color=brand) -> None:
            c.setFillColor(panel_2)
            c.roundRect(x, y, w, 6, 3, stroke=0, fill=1)
            fill_w = max(0, min(w, w * value / 100))
            if fill_w:
                c.setFillColor(color)
                c.roundRect(x, y, fill_w, 6, 3, stroke=0, fill=1)

        def draw_gauge(cx: float, cy: float, radius: float, value: int) -> None:
            c.setStrokeColor(colors.HexColor("#E4ECE9"))
            c.setLineWidth(14)
            c.circle(cx, cy, radius, stroke=1, fill=0)
            if value > 0:
                c.setStrokeColor(brand)
                c.setLineWidth(14)
                c.arc(cx - radius, cy - radius, cx + radius, cy + radius, 90, -360 * min(value, 100) / 100)
            set_font(36, ink)
            c.drawCentredString(cx, cy + 1, str(value))
            set_font(9, muted)
            c.drawCentredString(cx, cy - 16, "/ 100점")
            c.setFillColor(brand_soft)
            c.roundRect(cx - 28, cy - 38, 56, 16, 8, stroke=0, fill=1)
            set_font(8, brand)
            c.drawCentredString(cx, cy - 34, grade)

        def draw_sparkline(points: list[int], x: float, y: float, w: float, h: float, color) -> None:
            if len(points) < 2:
                return
            min_v = min(points)
            max_v = max(points)
            span = max(max_v - min_v, 1)
            step = w / (len(points) - 1)
            coords = []
            for idx, value in enumerate(points):
                px = x + idx * step
                py = y + h - ((value - min_v) / span) * h
                coords.append((px, py))
            c.setStrokeColor(color)
            c.setLineWidth(1.5)
            path = c.beginPath()
            path.moveTo(coords[0][0], coords[0][1])
            for px, py in coords[1:]:
                path.lineTo(px, py)
            c.drawPath(path, stroke=1, fill=0)

        def count_text(value: int, unit: str = "건") -> str:
            return f"{int(value)}{unit}"

        def metric_value(metric: dict[str, str]) -> int:
            raw = str(metric.get("value") or "0")
            digits = "".join(ch for ch in raw if ch.isdigit())
            return int(digits or "0")

        def performance_percent(metric: dict[str, str]) -> int:
            return min(100, metric_value(metric) * 20)

        set_font(18, ink)
        c.drawString(margin_x + 42, top_y - 6, "All4Health")
        set_font(8, muted)
        c.drawString(margin_x + 42, top_y - 22, "주간 건강 리포트 · Weekly Health Report")
        c.setFillColor(brand)
        c.roundRect(margin_x, top_y - 28, 30, 30, 9, stroke=0, fill=1)
        set_font(18, white)
        c.drawCentredString(margin_x + 15, top_y - 20, "♥")
        set_font(10, ink)
        c.drawRightString(
            page_width - margin_x, top_y - 3, f"{report.week_start_date:%Y.%m.%d} – {report.week_end_date:%m.%d}"
        )
        set_font(8, muted)
        c.drawRightString(page_width - margin_x, top_y - 18, f"Report #{report_no}")
        c.setStrokeColor(line)
        c.line(margin_x, top_y - 42, page_width - margin_x, top_y - 42)

        hero_y = top_y - 205
        draw_round_rect(margin_x, hero_y, content_width, 145, colors.HexColor("#F4F8F6"), line, 18)
        draw_gauge(margin_x + 96, hero_y + 75, 54, score)
        vitals_x = margin_x + 210
        vital_items = [
            ("건강 기록", count_text(total_records), [2, 4, 3, max(total_records, 1), 5], red, "입력된 검사·건강 수치"),
            (
                "AI 위험 신호",
                count_text(source.get("at_risk_prediction_count", 0)),
                [1, 1, 2, 1, max(source.get("at_risk_prediction_count", 0), 1)],
                orange,
                "이번 주 예측 결과",
            ),
            (
                "총 운동 기록",
                count_text(source.get("exercise_log_count", 0)),
                [1, 2, 1, 3, max(source.get("exercise_log_count", 0), 1)],
                brand,
                "전주 대비 실천 확인",
            ),
            (
                "생활습관 기록",
                count_text(source.get("activity_log_count", 0)),
                [1, 2, 2, 3, max(source.get("activity_log_count", 0), 1)],
                violet,
                "수면·수분·활동 기록",
            ),
        ]
        for idx, (label, value, spark, color, delta) in enumerate(vital_items):
            col = idx % 2
            row = idx // 2
            x = vitals_x + col * 130
            y = hero_y + 104 - row * 58
            c.setFillColor(color)
            c.circle(x, y + 4, 3, stroke=0, fill=1)
            set_font(8.5, ink_2)
            c.drawString(x + 8, y, label)
            set_font(18, ink)
            c.drawString(x, y - 23, value)
            draw_sparkline(spark, x + 70, y - 26, 46, 18, color)
            set_font(7.2, muted)
            c.drawString(x, y - 38, delta)

        y = hero_y - 30
        y = draw_section_header(
            y, "Trends", "활력 징후 추이", f"{report.week_start_date:%m/%d}–{report.week_end_date:%m/%d}"
        )
        chart_h = 77
        for idx, (title, color, values, normal_text) in enumerate(
            [
                ("혈압·혈당 기록", red, [1, 2, 1, 3, 2, 4, source.get("vital_record_count", 0)], "주간 기록 건수 기준"),
                (
                    "건강 활동 기록",
                    orange,
                    [1, 1, 2, 2, 3, 3, source.get("activity_log_count", 0)],
                    "생활습관·운동 기록 기준",
                ),
            ]
        ):
            cy = y - idx * (chart_h + 10)
            draw_round_rect(margin_x, cy - chart_h, content_width, chart_h, white, line, 10)
            set_font(9, color)
            c.drawString(margin_x + 14, cy - 18, title)
            set_font(7.5, muted)
            c.drawRightString(page_width - margin_x - 14, cy - 18, normal_text)
            c.setStrokeColor(line)
            for grid in range(3):
                gy = cy - 32 - grid * 15
                c.line(margin_x + 42, gy, page_width - margin_x - 16, gy)
            draw_sparkline(values, margin_x + 52, cy - 66, content_width - 86, 34, color)
        y -= chart_h * 2 + 28

        y = draw_section_header(y, "Performance", "관리 영역별 성과")
        for metric in metric_summaries[:5]:
            label = str(metric.get("label") or "")
            percent = performance_percent(metric)
            set_font(9, ink_2)
            c.drawString(margin_x, y, label)
            set_font(9, ink)
            c.drawRightString(page_width - margin_x, y, f"{percent}%")
            draw_progress(margin_x, y - 12, content_width, percent, brand)
            y -= 30

        draw_footer(1)
        c.showPage()

        y = page_height - 48
        y = draw_section_header(y, "AI Summary", "AI 분석 요약")
        draw_round_rect(margin_x, y - 96, content_width, 96, white, line, 12)
        summary_y = draw_wrapped(
            report.report_text or "이번 주 건강 기록을 바탕으로 리포트를 생성했습니다.",
            margin_x + 16,
            y - 20,
            content_width - 32,
            9,
            14,
            ink_2,
        )
        facts = [
            f"건강 기록 {total_records}건",
            f"AI 예측 {source.get('prediction_count', 0)}건",
            f"식단 기록 {source.get('meal_log_count', 0)}건",
            f"챌린지 체크인 {source.get('challenge_checkin_count', 0)}회",
        ]
        set_font(8.2, ink_2)
        for idx, fact in enumerate(facts):
            c.drawString(margin_x + 18 + (idx % 2) * 240, summary_y - 2 - (idx // 2) * 14, f"· {fact}")
        y -= 126

        y = draw_section_header(y, "Goals", "주간 목표 달성률")
        donut_x = margin_x + 78
        donut_y = y - 76
        c.setStrokeColor(panel_2)
        c.setLineWidth(13)
        c.circle(donut_x, donut_y, 48, stroke=1, fill=0)
        if challenge_rate > 0:
            c.setStrokeColor(brand)
            c.arc(donut_x - 48, donut_y - 48, donut_x + 48, donut_y + 48, 90, -360 * min(challenge_rate, 100) / 100)
        set_font(24, ink)
        c.drawCentredString(donut_x, donut_y + 2, f"{challenge_rate}%")
        set_font(8, muted)
        c.drawCentredString(donut_x, donut_y - 16, "목표 달성")

        goal_x = margin_x + 170
        goal_items = [
            ("혈압·혈당", source.get("vital_record_count", 0), 3),
            ("식단 기록", source.get("meal_log_count", 0), 5),
            ("운동 기록", source.get("exercise_log_count", 0), 3),
            ("생활습관", source.get("activity_log_count", 0), 5),
            ("챌린지", source.get("challenge_checkin_count", 0), 3),
        ]
        for idx, (label, count, target) in enumerate(goal_items):
            gy = y - 18 - idx * 24
            pct = min(100, count / target * 100 if target else 0)
            set_font(8.5, ink_2)
            c.drawString(goal_x, gy, label)
            set_font(8.2, muted)
            c.drawRightString(page_width - margin_x, gy, f"{count} / {target}회")
            draw_progress(goal_x, gy - 9, content_width - 170, pct, brand if pct >= 100 else warn)
        y -= 150

        y = draw_section_header(y, "Daily Log", "일별 건강 지수")
        table_h = 25 + max(3, min(7, len(metric_summaries))) * 24
        draw_round_rect(margin_x, y - table_h, content_width, table_h, white, line, 10)
        c.setFillColor(panel)
        c.roundRect(margin_x, y - 25, content_width, 25, 10, stroke=0, fill=1)
        headers = [
            ("영역", margin_x + 14),
            ("기록", margin_x + 120),
            ("상태", margin_x + 205),
            ("설명", margin_x + 285),
        ]
        set_font(8, ink_2)
        for header, hx in headers:
            c.drawString(hx, y - 16, header)
        row_y = y - 25
        for idx, metric in enumerate(metric_summaries[:7]):
            row_y -= 24
            if idx % 2 == 0:
                c.setFillColor(colors.HexColor("#FCFDFC"))
                c.rect(margin_x, row_y, content_width, 24, stroke=0, fill=1)
            set_font(8.3, ink)
            c.drawString(margin_x + 14, row_y + 8, str(metric.get("label") or ""))
            c.drawString(margin_x + 120, row_y + 8, f"{metric.get('value', '')}{metric.get('unit') or ''}")
            draw_pill(margin_x + 205, row_y + 5, "", metric.get("status"))
            set_font(7.5, muted)
            c.drawString(
                margin_x + 285, row_y + 8, WeeklyReportService._limit_text(str(metric.get("description") or ""), 36)
            )
        y -= table_h + 30

        y = draw_section_header(y, "Insights", "건강 조언")
        card_w = (content_width - 14) / 2
        advice_h = 76
        draw_round_rect(margin_x, y - advice_h, card_w, advice_h, red_soft, colors.HexColor("#F3D2CE"), 12)
        set_font(9.5, red)
        c.drawString(margin_x + 14, y - 18, "주의할 점")
        draw_wrapped(
            "혈압·혈당 수치를 주기적으로 확인하세요. 식단과 운동 기록을 꾸준히 남기면 리포트 정확도가 높아집니다.",
            margin_x + 14,
            y - 36,
            card_w - 28,
            8,
            12,
            ink_2,
        )
        draw_round_rect(
            margin_x + card_w + 14, y - advice_h, card_w, advice_h, brand_soft, colors.HexColor("#CCE6DD"), 12
        )
        set_font(9.5, brand_dark)
        c.drawString(margin_x + card_w + 28, y - 18, "잘하고 있는 점")
        good_message = f"{challenge.get('message', '이번 주 생활습관 실천 내용을 확인했습니다.')} {trend.get('message', '다음 리포트에서 추이를 비교할 수 있습니다.')}"
        draw_wrapped(
            good_message,
            margin_x + card_w + 28,
            y - 36,
            card_w - 28,
            8,
            12,
            ink_2,
        )
        y -= advice_h + 30

        y = draw_section_header(y, "Next Steps", "다음 단계")
        next_steps = ["주 4회 이상 유산소 운동 기록", "나트륨 섭취 줄이기", "정기적인 혈압·혈당 모니터링"]
        for idx, step in enumerate(next_steps):
            box_y = y - idx * 30 - 22
            draw_round_rect(margin_x, box_y, content_width, 24, white, line, 8)
            c.setFillColor(brand)
            c.roundRect(margin_x + 12, box_y + 5, 16, 16, 5, stroke=0, fill=1)
            set_font(8, white)
            c.drawCentredString(margin_x + 20, box_y + 9, str(idx + 1))
            set_font(9, ink_2)
            c.drawString(margin_x + 40, box_y + 8, step)

        draw_footer(2)
        c.save()
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
