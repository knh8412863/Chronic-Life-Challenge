from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status

from app.dtos.reports import WeeklyReportGenerateRequest, WeeklyReportResponse, WeeklyReportSourceSummaryResponse
from app.models.challenges import ChallengeCheckin
from app.models.predictions import ChronicHealthInput, LipidObesityRecord, PredictionResult, RenalRecord
from app.models.reports import WeeklyReport
from app.models.users import User

RULE_BASED_PROVIDER = "RULE_BASED"
RULE_BASED_MODEL = "weekly-report-rules-v1"


class WeeklyReportService:
    async def generate_current_week(self, user: User, data: WeeklyReportGenerateRequest) -> WeeklyReportResponse:
        week_start, week_end = self._week_range()
        existing = await WeeklyReport.get_or_none(user_id=user.id, week_start_date=week_start)
        if existing and not data.force_regenerate:
            return self._to_response(existing, generated=False)
        if existing and data.force_regenerate:
            await existing.delete()

        source_summary = await self._build_source_summary(user.id, week_start, week_end)
        report = await WeeklyReport.create(
            user=user,
            week_start_date=week_start,
            week_end_date=week_end,
            source_summary=source_summary,
            report_text=self._build_report_text(source_summary),
            provider=RULE_BASED_PROVIDER,
            model_name=RULE_BASED_MODEL,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
        )
        return self._to_response(report, generated=True)

    async def get_current_week(self, user: User) -> WeeklyReportResponse:
        week_start, _ = self._week_range()
        report = await WeeklyReport.get_or_none(user_id=user.id, week_start_date=week_start)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이번 주 리포트를 찾을 수 없습니다.")
        return self._to_response(report, generated=False)

    async def get_report(self, user: User, report_id: int) -> WeeklyReportResponse:
        report = await WeeklyReport.get_or_none(id=report_id, user_id=user.id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주간 리포트를 찾을 수 없습니다.")
        return self._to_response(report, generated=False)

    async def get_reports(self, user: User, limit: int = 20) -> list[WeeklyReportResponse]:
        reports = await WeeklyReport.filter(user_id=user.id).order_by("-week_start_date").limit(limit)
        return [self._to_response(report, generated=False) for report in reports]

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
            "prediction_count": len(predictions),
            "at_risk_prediction_count": sum(
                1 for prediction in predictions if any(item.is_at_risk for item in prediction.items)
            ),
            "challenge_checkin_count": challenge_checkin_count,
        }

    @staticmethod
    def _build_report_text(source_summary: dict[str, int]) -> str:
        total_health_records = (
            source_summary["health_survey_count"]
            + source_summary["lipid_obesity_record_count"]
            + source_summary["renal_record_count"]
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
            source_summary=WeeklyReportSourceSummaryResponse(**report.source_summary),
            report_text=report.report_text,
            provider=report.provider,
            model_name=report.model_name,
            generated=generated,
            created_at=report.created_at,
            source_type="RULE_BASED",
        )
