from datetime import date, datetime
from types import SimpleNamespace

from app.dtos.challenges import ChallengeDisplayCategory, ChallengeParticipationStatus
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
    assert result.category == ChallengeDisplayCategory.COMPREHENSIVE
    assert result.duration_days == 7
    assert result.difficulty == "EASY"
    assert result.reward_points == 5


def test_challenge_summary_includes_card_status_fields():
    challenge = SimpleNamespace(
        id=2,
        title="걷기 챌린지",
        description="매일 걷기 목표를 달성합니다.",
        category="EXERCISE",
        target_metric="STEPS",
        goal_value=5000,
        duration_days=14,
    )

    result = ChallengeService._to_summary(
        challenge,
        is_joined=True,
        today_checked=True,
        participant_count=12,
    )

    assert result.participant_count == 12
    assert result.category == ChallengeDisplayCategory.EXERCISE
    assert result.today_checked is True
    assert result.difficulty == "NORMAL"
    assert result.reward_points == 10


def test_challenge_display_category_maps_frontend_values():
    assert ChallengeService._display_category(SimpleNamespace(category="HYDRATION", target_metric="WATER")) == "WATER"
    assert ChallengeService._display_category(SimpleNamespace(category="ANY", target_metric="STEPS")) == "WALK"
    assert (
        ChallengeService._display_category(SimpleNamespace(category="BLOOD_PRESSURE", target_metric="DAILY_CHECKIN"))
        == "COMPREHENSIVE"
    )


def test_challenge_summaries_can_be_sorted_by_popularity_and_duration():
    summaries = [
        SimpleNamespace(challenge_id=1, participant_count=2, duration_days=14),
        SimpleNamespace(challenge_id=2, participant_count=5, duration_days=30),
        SimpleNamespace(challenge_id=3, participant_count=5, duration_days=7),
    ]

    popular = ChallengeService._sort_challenge_summaries(summaries, "POPULAR")
    duration = ChallengeService._sort_challenge_summaries(summaries, "DURATION")

    assert [item.challenge_id for item in popular] == [2, 3, 1]
    assert [item.challenge_id for item in duration] == [3, 1, 2]


def test_challenge_recommendations_prioritize_managed_disease_tags():
    challenges = [
        SimpleNamespace(challenge_id=1, participant_count=10),
        SimpleNamespace(challenge_id=2, participant_count=20),
        SimpleNamespace(challenge_id=3, participant_count=30),
        SimpleNamespace(challenge_id=4, participant_count=40),
    ]
    tagged_rows = [
        {"challenge_id": 1, "disease_code": "DIABETES", "priority": 20},
        {"challenge_id": 2, "disease_code": "HYPERTENSION", "priority": 10},
        {"challenge_id": 3, "disease_code": "DIABETES", "priority": 10},
    ]

    ranked_ids = ChallengeService._rank_challenge_ids_by_disease_tags(
        tagged_rows,
        managed_diseases=["DIABETES", "HYPERTENSION"],
    )
    result = ChallengeService._rank_recommendations_by_tags(challenges, ranked_ids)

    assert [item.challenge_id for item in result] == [3, 1, 2, 4]


def test_challenge_detail_calculates_average_completion_and_guides():
    challenge = SimpleNamespace(
        target_metric="WATER",
        goal_value=8,
        duration_days=10,
    )
    participations = [
        SimpleNamespace(progress_count=5, challenge=SimpleNamespace(duration_days=10)),
        SimpleNamespace(progress_count=7, challenge=SimpleNamespace(duration_days=10)),
    ]

    assert ChallengeService._average_completion_rate(participations) == 60.0
    assert ChallengeService._difficulty(30) == "HARD"
    assert ChallengeService._reward_points(30) == 15
    assert ChallengeService._mission_text(challenge) == "물 섭취 8 달성하기"
    assert len(ChallengeService._how_to_join_steps(challenge)) == 3
    assert ChallengeService._daily_mission_examples(challenge)[0] == "물 섭취 8 달성하기"


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


def test_my_challenge_response_detects_today_health_context():
    today = date(2026, 6, 2)
    participation = SimpleNamespace(
        id=5,
        challenge=SimpleNamespace(id=2, title="물 챌린지", duration_days=5, target_metric="WATER", goal_value=8),
        status="JOINED",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5),
        progress_count=2,
        checkins=[],
    )

    result = ChallengeService._to_my_challenge(participation, today, {"water_ml": 2000})

    assert result.today_checked is True


def test_challenge_health_context_satisfies_goal_metrics():
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="STEPS", goal_value=6000),
        {"steps": 6200},
    )
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="WATER", goal_value=8),
        {"water_ml": 2000},
    )
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="EXERCISE", goal_value=30),
        {"exercise_minutes": 30},
    )
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="DIET", goal_value=1),
        {"meal_count": 1},
    )
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="DAILY_CHECKIN", goal_value=1),
        {"health_record_count": 1},
    )


def test_step_challenge_accepts_walking_minutes_as_completion():
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="STEPS", goal_value=6000),
        {"steps": 0, "walking_minutes": 30},
    )
    assert ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="STEPS", goal_value=6000),
        {"steps": 0, "walking_minutes": 45},
    )


def test_challenge_health_context_rejects_unmet_goal_metrics():
    assert not ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="STEPS", goal_value=6000),
        {"steps": 5000, "walking_minutes": 29},
    )
    assert not ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="WATER", goal_value=8),
        {"water_ml": 1500},
    )
    assert not ChallengeService._health_context_satisfies_challenge(
        SimpleNamespace(target_metric="UNKNOWN", goal_value=1),
        {"health_record_count": 1},
    )


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


def test_challenge_cancel_response_uses_updated_at_as_canceled_at():
    canceled_at = datetime(2026, 6, 2, 15, 20)
    participation = SimpleNamespace(
        id=8,
        challenge_id=3,
        status="CANCELED",
        updated_at=canceled_at,
    )

    response = ChallengeService._to_cancel_response(participation)

    assert response.participation_id == 8
    assert response.challenge_id == 3
    assert response.status == ChallengeParticipationStatus.CANCELED
    assert response.canceled_at == canceled_at


def test_challenge_badges_use_current_streak_progress():
    today = date(2026, 6, 5)
    checkins = [
        SimpleNamespace(checkin_date=date(2026, 6, 5), created_at=datetime(2026, 6, 5, 9, 0)),
        SimpleNamespace(checkin_date=date(2026, 6, 4), created_at=datetime(2026, 6, 4, 9, 0)),
        SimpleNamespace(checkin_date=date(2026, 6, 3), created_at=datetime(2026, 6, 3, 9, 0)),
    ]
    earned_badges = [
        SimpleNamespace(badge_type="STREAK_3", earned_at=datetime(2026, 6, 5, 9, 0)),
    ]

    result = ChallengeService._build_badge_list(checkins, today, "ALL", earned_badges)

    assert result.earned_count == 1
    assert result.total_completion_rate == 33.3
    assert result.items[0].badge_type == "STREAK_3"
    assert result.items[0].is_earned is True
    assert result.items[1].progress_rate == 42.9
    assert len(result.recent_earned) == 1


def test_challenge_badges_can_be_filtered_by_badge_type():
    today = date(2026, 6, 5)
    checkins = [
        SimpleNamespace(checkin_date=date(2026, 6, 5), created_at=datetime(2026, 6, 5, 9, 0)),
        SimpleNamespace(checkin_date=date(2026, 6, 4), created_at=datetime(2026, 6, 4, 9, 0)),
        SimpleNamespace(checkin_date=date(2026, 6, 3), created_at=datetime(2026, 6, 3, 9, 0)),
    ]

    result = ChallengeService._build_badge_list(checkins, today, "STREAK_7")

    assert len(result.items) == 1
    assert result.items[0].badge_type == "STREAK_7"


def test_challenge_weekly_leaderboard_ranks_users_and_masks_names():
    entries = [
        SimpleNamespace(rank_no=1, user_id=2, nickname_masked="김*현", total_points=20, completed_mission_count=2),
        SimpleNamespace(rank_no=2, user_id=1, nickname_masked="이*", total_points=10, completed_mission_count=1),
        SimpleNamespace(rank_no=3, user_id=3, nickname_masked="*", total_points=10, completed_mission_count=1),
    ]

    result = ChallengeService._build_weekly_leaderboard(
        entries=entries,
        my_entry=entries[1],
        current_user_id=1,
        week_start=date(2026, 6, 1),
        week_end=date(2026, 6, 7),
    )

    assert [item.user_id for item in result.items] == [2, 1, 3]
    assert result.items[0].rank == 1
    assert result.items[0].nickname_masked == "김*현"
    assert result.items[0].score == 20
    assert result.my_rank.rank == 2
    assert result.my_rank.completed_mission_count == 1


def test_challenge_dashboard_summary_counts_active_completed_and_today_missions():
    today = date(2026, 6, 3)
    week_start = date(2026, 6, 1)
    week_end = date(2026, 6, 7)
    participations = [
        SimpleNamespace(
            id=1,
            status="JOINED",
            challenge=SimpleNamespace(id=10, title="걷기 챌린지", target_metric="STEPS", goal_value=5000),
            checkins=[
                SimpleNamespace(checkin_date=date(2026, 6, 1)),
                SimpleNamespace(checkin_date=date(2026, 6, 2)),
                SimpleNamespace(checkin_date=today),
            ],
        ),
        SimpleNamespace(
            id=2,
            status="JOINED",
            challenge=SimpleNamespace(id=11, title="물 마시기", target_metric="WATER", goal_value=8),
            checkins=[],
        ),
        SimpleNamespace(
            id=3,
            status="COMPLETED",
            challenge=SimpleNamespace(id=12, title="수면 챌린지", target_metric="SLEEP", goal_value=7),
            checkins=[SimpleNamespace(checkin_date=date(2026, 6, 1))],
        ),
    ]

    result = ChallengeService._build_dashboard_summary(participations, today, week_start, week_end)

    assert result.active_count == 2
    assert result.completed_count == 1
    assert result.completed_mission_count == 4
    assert result.weekly_completion_rate == 66.7
    assert result.current_streak_days == 3
    assert result.earned_badge_count == 0
    assert len(result.today_missions) == 2
    assert result.today_missions[0].today_checked is True
    assert result.today_missions[0].mission_text == "걸음 수 5000 달성하기"


def test_challenge_dashboard_summary_marks_multiple_today_missions_from_health_context():
    today = date(2026, 6, 3)
    week_start = date(2026, 6, 1)
    week_end = date(2026, 6, 7)
    participations = [
        SimpleNamespace(
            id=1,
            status="JOINED",
            challenge=SimpleNamespace(id=10, title="걷기 챌린지", target_metric="STEPS", goal_value=5000),
            checkins=[],
        ),
        SimpleNamespace(
            id=2,
            status="JOINED",
            challenge=SimpleNamespace(id=11, title="물 마시기", target_metric="WATER", goal_value=8),
            checkins=[],
        ),
    ]

    result = ChallengeService._build_dashboard_summary(
        participations,
        today,
        week_start,
        week_end,
        today_context={"steps": 6000, "water_ml": 2000},
    )

    assert [mission.today_checked for mission in result.today_missions] == [True, True]


def test_challenge_dashboard_summary_returns_empty_state():
    today = date(2026, 6, 3)
    week_start = date(2026, 6, 1)
    week_end = date(2026, 6, 7)

    result = ChallengeService._build_dashboard_summary([], today, week_start, week_end)

    assert result.active_count == 0
    assert result.completed_count == 0
    assert result.weekly_completion_rate == 0.0
    assert result.current_streak_days == 0
    assert result.completed_mission_count == 0
    assert result.today_missions == []
    assert len(result.weekly_activity) == 7


def test_home_challenge_summary_uses_average_completion_rate():
    participations = [
        SimpleNamespace(progress_count=3, challenge=SimpleNamespace(duration_days=10)),
        SimpleNamespace(progress_count=5, challenge=SimpleNamespace(duration_days=10)),
    ]

    result = HomeService._build_challenge_summary(participations)

    assert result.active_count == 2
    assert result.completion_rate == 40.0
    assert result.message == "진행 중인 챌린지 2개가 있습니다."
