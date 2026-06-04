from fastapi import HTTPException, status
from tortoise import timezone

from app.dtos.notifications import (
    NotificationMarkAllReadResponse,
    NotificationMarkReadResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationResponse,
    NotificationType,
    NotificationUnreadCountResponse,
)
from app.models.notifications import Notification, NotificationPreference
from app.models.users import User

PUSH_DETAIL_FIELDS = {
    "health_data_reminder_enabled",
    "challenge_mission_enabled",
    "prediction_result_enabled",
    "advice_update_enabled",
    "virtual_pet_enabled",
}


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

    async def get_preferences(self, user: User) -> NotificationPreferenceResponse:
        preference = await self._get_or_create_preference(user)
        return self._to_preference_response(preference)

    async def update_preferences(
        self,
        user: User,
        data: NotificationPreferenceUpdateRequest,
    ) -> NotificationPreferenceResponse:
        preference = await self._get_or_create_preference(user)
        payload = self._normalize_preference_update(data.model_dump(exclude_none=True))
        for field, value in payload.items():
            setattr(preference, field, value)
        await preference.save(update_fields=[*payload.keys(), "updated_at"] if payload else ["updated_at"])
        return self._to_preference_response(preference)

    @staticmethod
    async def count_unread(user_id: int) -> int:
        return await Notification.filter(user_id=user_id, is_read=False).count()

    @staticmethod
    async def _get_or_create_preference(user: User) -> NotificationPreference:
        preference, _ = await NotificationPreference.get_or_create(user_id=user.id)
        return preference

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

    @staticmethod
    def _normalize_preference_update(payload: dict) -> dict:
        if payload.get("push_enabled") is False:
            for field in PUSH_DETAIL_FIELDS:
                payload[field] = False
        return payload

    @staticmethod
    def _to_preference_response(preference: NotificationPreference) -> NotificationPreferenceResponse:
        return NotificationPreferenceResponse(
            push_enabled=preference.push_enabled,
            health_data_reminder_enabled=preference.health_data_reminder_enabled,
            challenge_mission_enabled=preference.challenge_mission_enabled,
            prediction_result_enabled=preference.prediction_result_enabled,
            advice_update_enabled=preference.advice_update_enabled,
            virtual_pet_enabled=preference.virtual_pet_enabled,
            email_enabled=preference.email_enabled,
            weekly_report_enabled=preference.weekly_report_enabled,
            important_notice_enabled=preference.important_notice_enabled,
            promotion_enabled=preference.promotion_enabled,
            quiet_start_time=preference.quiet_start_time,
            quiet_end_time=preference.quiet_end_time,
        )
