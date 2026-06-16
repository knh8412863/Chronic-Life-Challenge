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

        source = report.source_summary
        summary_cards = report.summary_cards or []
        metric_summaries = report.metric_summaries or []
        challenge = report.challenge_summary or {}
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
        trend_points = [18, 32, 24, 38, 30, 44, 35]
        trend_polyline = " ".join(f"{index * 58 + 20},{70 - value}" for index, value in enumerate(trend_points))
        metric_rows = []
        for metric in metric_summaries:
            value = f"{metric.get('value', '0')}{metric.get('unit') or ''}"
            status_value = status_label(metric.get("status"))
            metric_rows.append(
                f"""
                <tr>
                  <td>{esc(metric.get("label"))}</td>
                  <td>{esc(value)}</td>
                  <td>{esc(status_value)}</td>
                  <td>{esc(metric.get("description"))}</td>
                </tr>
                """
            )

        card_html = []
        colors = ["#ff4d3d", "#ff9900", "#14a85b", "#8b5cf6", "#333333"]
        for index, card in enumerate(summary_cards[:5]):
            card_html.append(
                f"""
                <article class="metric-card">
                  <p>{esc(card.get("label"))}</p>
                  <strong style="color:{colors[index % len(colors)]}">{esc(card.get("value"))}</strong>
                  <small>{esc(status_label(card.get("status")))}</small>
                </article>
                """
            )

        metric_bars = []
        for metric in metric_summaries[:5]:
            raw_value = int("".join(ch for ch in str(metric.get("value", "0")) if ch.isdigit()) or "0")
            width = min(100, max(12, raw_value * 12))
            metric_bars.append(
                f"""
                <div class="bar-row">
                  <span>{esc(metric.get("label"))}</span>
                  <b>{esc(metric.get("value"))}{esc(metric.get("unit") or "")}</b>
                  <div><i style="width:{width}%"></i></div>
                </div>
                """
            )

        goal_lines = [
            ("혈압·혈당", source.get("vital_record_count", 0), "주 3회 이상"),
            ("식단 기록", source.get("meal_log_count", 0), "주 5회"),
            ("운동 기록", source.get("exercise_log_count", 0), "주 3회"),
            ("챌린지", source.get("challenge_checkin_count", 0), "주 3회 이상"),
        ]
        goal_html = "\n".join(
            f"<li>{'✓' if count else '△'} {esc(label)}: {esc(count)}회 / {esc(target)}</li>"
            for label, count, target in goal_lines
        )

        return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>All4Health 주간 리포트</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #f3f4f6;
      color: #222;
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
      line-height: 1.55;
    }}
    .page {{
      width: 760px;
      min-height: 1080px;
      margin: 24px auto;
      padding: 52px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      background: #fff;
    }}
    .hero {{ padding: 34px 38px; border-radius: 14px; background: #f1f2f5; margin-bottom: 38px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: -0.02em; }}
    h2 {{ margin: 34px 0 16px; font-size: 20px; }}
    p {{ margin: 0; }}
    .period {{ color: #555; font-size: 16px; }}
    .score {{ margin-top: 28px; font-size: 20px; font-weight: 800; }}
    .score strong {{ font-size: 26px; }}
    .formula {{ margin-top: 8px; color: #444; font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; margin-bottom: 28px; }}
    .metric-card {{ min-height: 126px; padding: 24px; border-radius: 12px; background: #f1f2f4; }}
    .metric-card p {{ margin-bottom: 12px; color: #333; font-size: 15px; }}
    .metric-card strong {{ display: block; font-size: 28px; line-height: 1.1; }}
    .metric-card small {{ display: block; margin-top: 8px; color: #555; font-size: 13px; }}
    .chart {{ height: 160px; padding: 20px; border-radius: 10px; background: #f1f2f4; }}
    .summary-box {{ padding: 24px; border-radius: 10px; background: #f4f5f8; white-space: pre-wrap; }}
    .bars {{ padding: 20px; border-radius: 10px; background: #f4f5f8; }}
    .bar-row {{ display: grid; grid-template-columns: 120px 60px 1fr; align-items: center; gap: 14px; margin-bottom: 14px; }}
    .bar-row span {{ color: #555; }}
    .bar-row b {{ text-align: right; }}
    .bar-row div {{ height: 8px; border-radius: 999px; background: #e5e7eb; overflow: hidden; }}
    .bar-row i {{ display: block; height: 100%; border-radius: 999px; background: #333; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th {{ background: #f0f1f3; text-align: left; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 7px 0; }}
    .notice {{ margin-top: 34px; padding: 18px 20px; border-radius: 10px; background: #f1f2f4; color: #444; }}
    .footer {{ display: flex; justify-content: space-between; margin-top: 34px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #c0c5cc; font-size: 12px; }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ width: auto; min-height: auto; margin: 0; border: 0; border-radius: 0; page-break-after: always; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <h1>All4Health</h1>
      <p class="period">주간 건강 리포트</p>
      <p class="period">{esc(report.week_start_date)} ~ {esc(report.week_end_date)}</p>
      <p class="score">종합 건강 점수: <strong>{score}점</strong></p>
      <p class="formula">점수 계산: 건강 기록 + 혈압·혈당 + 운동 + 식단 + 챌린지 실천을 종합 반영</p>
    </section>

    <section class="grid">
      {"".join(card_html)}
    </section>

    <h2>건강 추이</h2>
    <div class="chart">
      <svg viewBox="0 0 410 110" width="100%" height="100%" aria-label="건강 추이">
        <polyline points="{trend_polyline}" fill="none" stroke="#ff4d3d" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>

    <h2>AI 분석 요약</h2>
    <div class="summary-box">{esc(report.report_text)}</div>

    <h2>관리 영역별 성과</h2>
    <div class="bars">{"".join(metric_bars)}</div>

    <h2>목표 달성률: {completion_rate}%</h2>
    <ul>{goal_html}</ul>

    <h2>상세 분석</h2>
    <table>
      <thead><tr><th>영역</th><th>기록</th><th>상태</th><th>설명</th></tr></thead>
      <tbody>{"".join(metric_rows)}</tbody>
    </table>

    <h2>건강 조언</h2>
    <p><strong>주의할 점</strong></p>
    <ul>
      <li>혈압·혈당 수치를 주기적으로 확인하세요.</li>
      <li>식단과 운동 기록을 꾸준히 남기면 리포트 정확도가 높아집니다.</li>
    </ul>
    <p style="margin-top:18px"><strong>잘한 점</strong></p>
    <ul>
      <li>{esc(report.challenge_summary.get("message", "이번 주 생활습관 실천 내용을 확인했습니다."))}</li>
      <li>{esc(report.trend_summary.get("message", "다음 리포트에서 추이를 비교할 수 있습니다."))}</li>
    </ul>

    <h2>다음 단계</h2>
    <ol>
      <li>주 4회 이상 유산소 운동 기록</li>
      <li>나트륨 섭취 줄이기</li>
      <li>정기적인 혈압·혈당 모니터링</li>
    </ol>
    <div class="notice">{esc(REPORT_DISCLAIMER)}</div>
    <footer class="footer"><span>All4Health © 2026</span><span>주간 리포트</span></footer>
  </main>
</body>
</html>"""

    @staticmethod
    def _to_pdf_content(report: WeeklyReport) -> bytes:  # noqa: C901
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PDF 생성 모듈이 설치되지 않았습니다. 서버 의존성을 다시 설치해주세요.",
            ) from exc

        buffer = io.BytesIO()
        page_width, page_height = A4
        margin = 48
        content_w = page_width - margin * 2
        pdfmetrics.registerFont(UnicodeCIDFont("HYGothic-Medium"))
        fn = "HYGothic-Medium"
        cv = canvas.Canvas(buffer, pagesize=A4)

        C_GRN = colors.HexColor("#3D7A4F")
        C_GRN_D = colors.HexColor("#2D5A3D")
        C_GRN_M = colors.HexColor("#A8D5B5")
        C_RED = colors.HexColor("#E53935")
        C_ORG = colors.HexColor("#F57C00")
        C_PUR = colors.HexColor("#7B1FA2")
        C_TXT = colors.HexColor("#1A1A1A")
        C_MID = colors.HexColor("#555555")
        C_LIT = colors.HexColor("#888888")
        C_BDR = colors.HexColor("#E5E7EB")
        C_BG = colors.HexColor("#F8F9FA")
        C_WHT = colors.white
        CARD_COLS = [C_RED, C_ORG, colors.HexColor("#14A85B"), C_PUR]

        def sf(size: int, fill=None) -> None:
            cv.setFont(fn, size)
            cv.setFillColor(fill if fill is not None else C_TXT)

        def wrap(text: str, x: float, y: float, max_w: float, size: int, lead: int = 14, fill=None) -> float:
            sf(size, fill)
            for para in (str(text) or "").splitlines() or [""]:
                line = ""
                for word in para.split():
                    cand = word if not line else f"{line} {word}"
                    if pdfmetrics.stringWidth(cand, fn, size) <= max_w:
                        line = cand
                    else:
                        cv.drawString(x, y, line)
                        y -= lead
                        line = word
                cv.drawString(x, y, line)
                y -= lead
            return y

        def section_heading(title: str, y: float) -> float:
            sf(11, C_TXT)
            cv.drawString(margin, y, title)
            w = pdfmetrics.stringWidth(title, fn, 11)
            cv.setStrokeColor(C_GRN)
            cv.setLineWidth(2)
            cv.line(margin, y - 5, margin + w, y - 5)
            return y - 22

        def footer(page: int) -> None:
            cv.setStrokeColor(C_BDR)
            cv.setLineWidth(0.5)
            cv.line(margin, 38, page_width - margin, 38)
            sf(7.5, C_LIT)
            cv.drawString(margin, 24, "All4Health © 2026")
            cv.drawCentredString(page_width / 2, 24, REPORT_DISCLAIMER)
            cv.drawRightString(page_width - margin, 24, f"{page} / 2")

        source = getattr(report, "source_summary", None) or {}
        challenge = getattr(report, "challenge_summary", None) or {}
        trend = getattr(report, "trend_summary", None) or {}
        total_hr = WeeklyReportService._total_health_records(source)
        score = min(
            100,
            55
            + min(total_hr, 5) * 5
            + min(source.get("exercise_log_count", 0), 5) * 3
            + min(source.get("meal_log_count", 0), 5) * 2
            + min(source.get("challenge_checkin_count", 0), 7) * 2,
        )
        completion_rate = int(float(challenge.get("completion_rate") or 0))

        # ── PAGE 1 ──────────────────────────────────────────────────────────────
        hdr_h = 120
        cv.setFillColor(C_GRN)
        cv.rect(0, page_height - hdr_h, page_width, hdr_h, stroke=0, fill=1)

        sf(20, C_WHT)
        cv.drawString(margin, page_height - 36, "All4Health")
        sf(9, C_GRN_M)
        cv.drawString(margin, page_height - 54, "주간 건강 리포트")
        sf(8.5, colors.HexColor("#C8E6CE"))
        cv.drawString(margin, page_height - 70, f"{report.week_start_date}  ~  {report.week_end_date}")

        bx = page_width - margin - 88
        by = page_height - hdr_h + 16
        cv.setFillColor(C_GRN_D)
        cv.roundRect(bx, by, 88, 90, 8, stroke=0, fill=1)
        sf(8, C_GRN_M)
        cv.drawCentredString(bx + 44, by + 70, "종합 점수")
        sf(30, C_WHT)
        cv.drawCentredString(bx + 44, by + 34, str(score))
        sf(9, C_GRN_M)
        cv.drawCentredString(bx + 44, by + 16, "점")

        y = page_height - hdr_h - 28
        cards_src = (report.summary_cards or [])[:4]
        if cards_src:
            card_lv = [(d.get("label", ""), str(d.get("value", ""))) for d in cards_src]
        else:
            card_lv = [
                ("건강 기록", f"{total_hr}건"),
                ("AI 위험 신호", "—"),
                ("식단 기록", f"{source.get('meal_log_count', 0)}건"),
                ("운동 기록", f"{source.get('exercise_log_count', 0)}건"),
            ]
        card_w = (content_w - 12) / 2
        card_h = 64
        for idx, (lbl, val) in enumerate(card_lv[:4]):
            cax = margin + (idx % 2) * (card_w + 12)
            cay = y - (idx // 2) * (card_h + 10)
            accent = CARD_COLS[idx % len(CARD_COLS)]
            cv.setFillColor(C_BG)
            cv.roundRect(cax, cay - card_h, card_w, card_h, 6, stroke=0, fill=1)
            cv.setFillColor(accent)
            cv.roundRect(cax, cay - card_h, 4, card_h, 2, stroke=0, fill=1)
            sf(8, C_LIT)
            cv.drawString(cax + 14, cay - 18, lbl)
            sf(20, accent)
            cv.drawString(cax + 14, cay - 44, val)

        y -= (card_h + 10) * 2 + 24

        y = section_heading("AI 분석 요약", y)
        box_h = 88
        cv.setFillColor(C_BG)
        cv.roundRect(margin, y - box_h, content_w, box_h, 6, stroke=0, fill=1)
        cv.setStrokeColor(C_BDR)
        cv.setLineWidth(0.5)
        cv.roundRect(margin, y - box_h, content_w, box_h, 6, stroke=1, fill=0)
        wrap(report.report_text or "분석 내용 없음", margin + 14, y - 16, content_w - 28, 8.5, 13)
        y -= box_h + 22

        y = section_heading("관리 영역별 성과", y)
        bar_x = margin + 130
        bar_w = content_w - 130 - 4
        for metric in (report.metric_summaries or [])[:5]:
            lbl = str(metric.get("label", ""))
            val_s = str(metric.get("value", "0"))
            unit = metric.get("unit") or ""
            raw = int("".join(ch for ch in val_s if ch.isdigit()) or "0")
            sf(8.5, C_MID)
            cv.drawString(margin, y, lbl)
            sf(8.5, C_TXT)
            cv.drawRightString(bar_x - 6, y, f"{val_s}{unit}")
            cv.setFillColor(C_BDR)
            cv.roundRect(bar_x, y - 2, bar_w, 7, 3, stroke=0, fill=1)
            fill_w = min(bar_w, max(14, raw * 15))
            cv.setFillColor(C_GRN)
            cv.roundRect(bar_x, y - 2, fill_w, 7, 3, stroke=0, fill=1)
            y -= 20

        footer(1)
        cv.showPage()

        # ── PAGE 2 ──────────────────────────────────────────────────────────────
        y = page_height - 60

        y = section_heading("목표 달성률", y)
        sf(26, C_GRN)
        cv.drawString(margin, y, f"{completion_rate}%")
        sf(9, C_LIT)
        cv.drawString(margin + 52, y, "달성")
        y -= 26

        for lbl, count, target in [
            ("혈압·혈당", source.get("vital_record_count", 0), "주 3회 이상"),
            ("식단 기록", source.get("meal_log_count", 0), "주 5회"),
            ("운동 기록", source.get("exercise_log_count", 0), "주 3회"),
            ("챌린지", source.get("challenge_checkin_count", 0), "주 3회 이상"),
        ]:
            sf(9, C_GRN if count else C_ORG)
            cv.drawString(margin, y, "✓" if count else "△")
            sf(8.5, C_TXT)
            cv.drawString(margin + 16, y, f"{lbl}: {count}회")
            tw = pdfmetrics.stringWidth(f"{lbl}: {count}회", fn, 8.5)
            sf(8, C_LIT)
            cv.drawString(margin + 16 + tw + 8, y, f"/ {target}")
            y -= 16
        y -= 20

        y = section_heading("상세 분석", y)
        col_xs = [margin, margin + 110, margin + 178, margin + 248]
        cv.setFillColor(C_GRN)
        cv.roundRect(margin, y - 20, content_w, 22, 4, stroke=0, fill=1)
        sf(8.5, C_WHT)
        for xi, h in zip(col_xs, ["영역", "기록", "상태", "설명"]):
            cv.drawString(xi + 6, y - 14, h)
        y -= 26

        for idx, metric in enumerate((report.metric_summaries or [])[:7]):
            cv.setFillColor(C_BG if idx % 2 == 0 else C_WHT)
            cv.rect(margin, y - 24, content_w, 24, stroke=0, fill=1)
            sf(8, C_TXT)
            cv.drawString(col_xs[0] + 6, y - 15, str(metric.get("label", "")))
            cv.drawString(col_xs[1] + 6, y - 15, f"{metric.get('value', '')}{metric.get('unit') or ''}")
            status_v = str(metric.get("status", ""))
            sf(7.5, C_GRN if status_v == "NORMAL" else C_RED)
            cv.drawString(col_xs[2] + 6, y - 15, status_v)
            sf(7.5, C_MID)
            cv.drawString(col_xs[3] + 6, y - 15, str(metric.get("description", ""))[:42])
            cv.setStrokeColor(C_BDR)
            cv.setLineWidth(0.3)
            cv.line(margin, y - 24, page_width - margin, y - 24)
            y -= 24
        y -= 20

        y = section_heading("건강 조언", y)

        def advice_box(title: str, body: str, bg_hex: str, accent_col) -> None:
            nonlocal y
            cv.setFillColor(colors.HexColor(bg_hex))
            cv.roundRect(margin, y - 54, content_w, 56, 6, stroke=0, fill=1)
            cv.setFillColor(accent_col)
            cv.roundRect(margin, y - 54, 3, 56, 2, stroke=0, fill=1)
            sf(8.5, accent_col)
            cv.drawString(margin + 12, y - 13, title)
            wrap(body, margin + 12, y - 28, content_w - 20, 8, 13)
            y -= 68

        advice_box(
            "주의할 점",
            "혈압·혈당 수치를 주기적으로 확인하세요. 식단과 운동 기록을 꾸준히 남기면 리포트 정확도가 높아집니다.",
            "#FFF3F3",
            C_RED,
        )
        good_msg = (
            f"{challenge.get('message', '이번 주 생활습관 실천 내용을 확인했습니다.')}"
            f" {trend.get('message', '다음 리포트에서 추이를 비교할 수 있습니다.')}"
        )
        advice_box("잘한 점", good_msg, "#F0F9F3", C_GRN)
        y -= 6

        y = section_heading("다음 단계", y)
        for step_i, step_text in enumerate([
            "주 4회 이상 유산소 운동 기록",
            "나트륨 섭취 줄이기",
            "정기적인 혈압·혈당 모니터링",
        ]):
            cv.setFillColor(C_GRN)
            cv.circle(margin + 8, y - 2, 7, stroke=0, fill=1)
            sf(7.5, C_WHT)
            cv.drawCentredString(margin + 8, y - 5, str(step_i + 1))
            sf(8.5, C_TXT)
            cv.drawString(margin + 22, y - 3, step_text)
            y -= 20
        y -= 14

        cv.setFillColor(C_BG)
        cv.roundRect(margin, y - 26, content_w, 28, 6, stroke=0, fill=1)
        sf(7.5, C_LIT)
        cv.drawCentredString(page_width / 2, y - 14, REPORT_DISCLAIMER)

        footer(2)
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
