from datetime import date, datetime
from types import SimpleNamespace

from app.dtos.challenges import ChallengeParticipationStatus
from app.services.challenges import ChallengeService
from app.services.home import HomeService


def test_challenge_completion_rate_caps_at_one_hundred():
    assert ChallengeService._completion_rate(progress_count=3, duration_days=10) == 30.0
    assert ChallengeService._completion_rate(progress_count=12, duration_days=10) == 100.0
    assert ChallengeService._completion_rate(progress_count=1, duration_days=0) == 0.0


def test_challenge_summary_marks_joined_state():
    challenge = SimpleNamespace(
        id=1,
        title="혈압 기록 챌린지",
        description="매일 혈압을 기록합니다.",
        category="BLOOD_PRESSURE",
        target_metric="DAILY_CHECKIN",
        goal_value=1,
        duration_days=7,
    )

    result = ChallengeService._to_summary(challenge, is_joined=True)

    assert result.challenge_id == 1
    assert result.is_joined is True
    assert result.duration_days == 7


def test_my_challenge_response_detects_today_checkin():
    today = date(2026, 6, 2)
    participation = SimpleNamespace(
        id=5,
        challenge=SimpleNamespace(id=2, title="걷기 챌린지", duration_days=5),
        status="JOINED",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5),
        progress_count=2,
        checkins=[SimpleNamespace(checkin_date=today)],
    )

    result = ChallengeService._to_my_challenge(participation, today)

    assert result.participation_id == 5
    assert result.status == ChallengeParticipationStatus.JOINED
    assert result.today_checked is True
    assert result.completion_rate == 40.0


def test_challenge_checkin_response_can_mark_completed():
    checkin = SimpleNamespace(id=7, checkin_date=date(2026, 6, 2), created_at=datetime(2026, 6, 2, 14, 30))
    participation = SimpleNamespace(
        id=4,
        progress_count=7,
        status="COMPLETED",
        challenge=SimpleNamespace(duration_days=7),
    )

    response = ChallengeService._to_checkin_response(checkin, participation)

    assert response.checkin_id == 7
    assert response.status == ChallengeParticipationStatus.COMPLETED
    assert response.completion_rate == 100.0


def test_home_challenge_summary_uses_average_completion_rate():
    participations = [
        SimpleNamespace(progress_count=3, challenge=SimpleNamespace(duration_days=10)),
        SimpleNamespace(progress_count=5, challenge=SimpleNamespace(duration_days=10)),
    ]

    result = HomeService._build_challenge_summary(participations)

    assert result.active_count == 2
    assert result.completion_rate == 40.0
    assert result.message == "진행 중인 챌린지 2개가 있습니다."
