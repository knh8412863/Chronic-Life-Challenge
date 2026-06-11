from datetime import date, timedelta

from app.dtos.dashboard import (
    DashboardChallengeCalendarItemResponse,
    DashboardChallengeCalendarResponse,
    DashboardKoreaComparisonItemResponse,
    DashboardKoreaComparisonResponse,
    DashboardRiskTrendItemResponse,
    DashboardRiskTrendResponse,
)
from app.models.challenges import ChallengeCheckin
from app.models.predictions import LipidObesityRecord, PredictionResult, UserProfile
from app.models.users import User


class DashboardService:
    async def get_risk_trends(self, user: User, limit: int = 10) -> DashboardRiskTrendResponse:
        results = await PredictionResult.filter(user_id=user.id).order_by("-created_at").limit(limit).prefetch_related("items")
        items = [
            DashboardRiskTrendItemResponse(
                result_id=result.id,
                created_at=result.created_at,
                overall_risk_level=result.overall_risk_level,
                disease_risks={item.disease_code: float(item.probability) for item in result.items},
            )
            for result in results
        ]
        return DashboardRiskTrendResponse(items=items)

    async def get_challenge_calendars(
        self,
        user: User,
        from_date: date | None,
        to_date: date | None,
    ) -> DashboardChallengeCalendarResponse:
        end = to_date or date.today()
        start = from_date or end - timedelta(days=29)
        checkins = await ChallengeCheckin.filter(user_id=user.id, checkin_date__gte=start, checkin_date__lte=end)
        counts = {}
        for checkin in checkins:
            counts[checkin.checkin_date] = counts.get(checkin.checkin_date, 0) + 1
        items = []
        current = start
        while current <= end:
            items.append(DashboardChallengeCalendarItemResponse(activity_date=current, completed_count=counts.get(current, 0)))
            current += timedelta(days=1)
        return DashboardChallengeCalendarResponse(items=items)

    async def get_korea_comparisons(self, user: User) -> DashboardKoreaComparisonResponse:
        profile = await UserProfile.get_or_none(user_id=user.id)
        lipid = await LipidObesityRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        items = [
            DashboardKoreaComparisonItemResponse(
                metric="BMI",
                user_value=float(profile.bmi) if profile else None,
                comparison_value=23.0,
                unit="kg/m²",
                message="국내 일반 성인 BMI 기준 23 이상은 과체중 관리가 필요합니다.",
            ),
            DashboardKoreaComparisonItemResponse(
                metric="LDL_CHOLESTEROL",
                user_value=float(lipid.ldl_cholesterol) if lipid and lipid.ldl_cholesterol is not None else None,
                comparison_value=130.0,
                unit="mg/dL",
                message="LDL 콜레스테롤은 일반적으로 130mg/dL 미만 관리를 권장합니다.",
            ),
        ]
        return DashboardKoreaComparisonResponse(items=items)
