from datetime import datetime, time
from types import SimpleNamespace

from app.dtos.notifications import NotificationType
from app.services.notifications import NotificationService


def test_notification_response_maps_type_and_read_state():
    notification = SimpleNamespace(
        id=3,
        notification_type="CHALLENGE",
        title="챌린지 체크인",
        message="오늘 챌린지를 수행해 주세요.",
        link_url="/challenges",
        is_read=False,
        read_at=None,
        created_at=datetime(2026, 6, 2, 16, 0),
    )

    result = NotificationService._to_response(notification)

    assert result.notification_id == 3
    assert result.notification_type == NotificationType.CHALLENGE
    assert result.is_read is False
    assert result.link_url == "/challenges"


def test_mark_read_response_returns_read_timestamp():
    notification = SimpleNamespace(
        id=5,
        is_read=True,
        read_at=datetime(2026, 6, 2, 16, 10),
    )

    result = NotificationService._to_mark_read_response(notification)

    assert result.notification_id == 5
    assert result.is_read is True
    assert result.read_at == datetime(2026, 6, 2, 16, 10)


def test_notification_preference_response_maps_all_settings():
    preference = SimpleNamespace(
        push_enabled=True,
        health_data_reminder_enabled=True,
        challenge_mission_enabled=True,
        prediction_result_enabled=True,
        advice_update_enabled=False,
        virtual_pet_enabled=True,
        email_enabled=True,
        weekly_report_enabled=True,
        important_notice_enabled=True,
        promotion_enabled=False,
        quiet_start_time=time(9, 0),
        quiet_end_time=time(21, 0),
    )

    result = NotificationService._to_preference_response(preference)

    assert result.push_enabled is True
    assert result.advice_update_enabled is False
    assert result.email_enabled is True
    assert result.quiet_start_time == time(9, 0)
    assert result.quiet_end_time == time(21, 0)


def test_push_disabled_turns_off_push_detail_settings():
    payload = {
        "push_enabled": False,
        "health_data_reminder_enabled": True,
        "challenge_mission_enabled": True,
        "prediction_result_enabled": True,
        "advice_update_enabled": True,
        "virtual_pet_enabled": True,
    }

    result = NotificationService._normalize_preference_update(payload)

    assert result["push_enabled"] is False
    assert result["health_data_reminder_enabled"] is False
    assert result["challenge_mission_enabled"] is False
    assert result["prediction_result_enabled"] is False
    assert result["advice_update_enabled"] is False
    assert result["virtual_pet_enabled"] is False


def test_empty_notification_preference_update_keeps_payload_empty():
    result = NotificationService._normalize_preference_update({})

    assert result == {}


def test_push_enabled_does_not_force_push_detail_settings():
    payload = {
        "push_enabled": True,
        "health_data_reminder_enabled": False,
        "challenge_mission_enabled": True,
    }

    result = NotificationService._normalize_preference_update(payload)

    assert result["push_enabled"] is True
    assert result["health_data_reminder_enabled"] is False
    assert result["challenge_mission_enabled"] is True


def test_notification_preference_allows_prediction_when_enabled():
    preference = SimpleNamespace(
        push_enabled=True,
        prediction_result_enabled=True,
        challenge_mission_enabled=False,
        advice_update_enabled=False,
        weekly_report_enabled=False,
        important_notice_enabled=False,
    )

    assert NotificationService._preference_allows(preference, NotificationType.PREDICTION) is True
    assert NotificationService._preference_allows(preference, NotificationType.CHALLENGE) is False


def test_notification_preference_blocks_push_notifications_when_push_disabled():
    preference = SimpleNamespace(
        push_enabled=False,
        prediction_result_enabled=True,
        challenge_mission_enabled=True,
        advice_update_enabled=True,
        weekly_report_enabled=True,
        important_notice_enabled=True,
    )

    assert NotificationService._preference_allows(preference, NotificationType.PREDICTION) is False
    assert NotificationService._preference_allows(preference, NotificationType.ADVICE) is False
    assert NotificationService._preference_allows(preference, NotificationType.REPORT) is True
