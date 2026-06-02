from fastapi import HTTPException, status
from tortoise import timezone

from app.dtos.notifications import (
    NotificationMarkAllReadResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
    NotificationType,
    NotificationUnreadCountResponse,
)
from app.models.notifications import Notification
from app.models.users import User


class NotificationService:
    async def get_notifications(
        self, user: User, limit: int = 20, unread_only: bool = False
    ) -> list[NotificationResponse]:
        query = Notification.filter(user_id=user.id)
        if unread_only:
            query = query.filter(is_read=False)
        notifications = await query.order_by("-created_at").limit(limit)
        return [self._to_response(notification) for notification in notifications]

    async def get_unread_count(self, user: User) -> NotificationUnreadCountResponse:
        unread_count = await self.count_unread(user.id)
        return NotificationUnreadCountResponse(unread_count=unread_count)

    async def mark_read(self, user: User, notification_id: int) -> NotificationMarkReadResponse:
        notification = await Notification.get_or_none(id=notification_id, user_id=user.id)
        if notification is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")

        if not notification.is_read or notification.read_at is None:
            notification.is_read = True
            notification.read_at = timezone.now()
            await notification.save(update_fields=["is_read", "read_at"])

        return self._to_mark_read_response(notification)

    async def mark_all_read(self, user: User) -> NotificationMarkAllReadResponse:
        now = timezone.now()
        updated_count = await Notification.filter(user_id=user.id, is_read=False).update(is_read=True, read_at=now)
        return NotificationMarkAllReadResponse(updated_count=updated_count)

    @staticmethod
    async def count_unread(user_id: int) -> int:
        return await Notification.filter(user_id=user_id, is_read=False).count()

    @staticmethod
    def _to_response(notification: Notification) -> NotificationResponse:
        return NotificationResponse(
            notification_id=notification.id,
            notification_type=NotificationType(notification.notification_type),
            title=notification.title,
            message=notification.message,
            link_url=notification.link_url,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
        )

    @staticmethod
    def _to_mark_read_response(notification: Notification) -> NotificationMarkReadResponse:
        return NotificationMarkReadResponse(
            notification_id=notification.id,
            is_read=notification.is_read,
            read_at=notification.read_at,
        )
