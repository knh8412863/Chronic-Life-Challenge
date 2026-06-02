from datetime import datetime
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
