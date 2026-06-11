from datetime import date, timedelta

from app.dtos.scores import HealthScoreHistoryResponse, HealthScoreResponse
from app.models.users import User
from app.services.home import HomeService


class ScoreService:
    async def get_today_score(self, user: User) -> HealthScoreResponse:
        return await self._score_for_date(user, date.today())

    async def get_scores(self, user: User, from_date: date | None, to_date: date | None) -> HealthScoreHistoryResponse:
        end = to_date or date.today()
        start = from_date or end - timedelta(days=6)
        items = []
        current = start
        while current <= end:
            items.append(await self._score_for_date(user, current))
            current += timedelta(days=1)
        return HealthScoreHistoryResponse(items=items)

    @staticmethod
    async def _score_for_date(user: User, target_date: date) -> HealthScoreResponse:
        summary = await HomeService().get_summary(user)
        score = summary.today_score.score
        grade = None
        if score is not None:
            if score >= 90:
                grade = "S"
            elif score >= 80:
                grade = "A"
            elif score >= 70:
                grade = "B"
            elif score >= 60:
                grade = "C"
            else:
                grade = "D"
        return HealthScoreResponse(
            score_date=target_date,
            total_score=score,
            grade=grade,
            status=summary.today_score.status,
            message=summary.today_score.message,
            calculation_basis=summary.today_score.calculation_basis,
        )
