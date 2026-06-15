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
    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        link_url: str | None = None,
    ) -> Notification | None:
        preference = await NotificationPreference.get_or_none(user_id=user_id)
        if preference is not None and not self._preference_allows(preference, notification_type):
            return None

        return await Notification.create(
            user_id=user_id,
            notification_type=notification_type.value,
            title=title,
            message=message,
            link_url=link_url,
        )

    async def notify_prediction_result(
        self, user_id: int, result_id: int, overall_risk_level: str
    ) -> Notification | None:
        is_high = overall_risk_level == "HIGH"
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.PREDICTION,
            title="예측 결과가 도착했습니다.",
            message=(
                "고위험 신호가 포함된 예측 결과가 있습니다. 결과를 확인해 주세요."
                if is_high
                else "새로운 질환 예측 결과를 확인할 수 있습니다."
            ),
            link_url=f"/prediction/result?result_id={result_id}",
        )

    async def notify_advice_created(self, user_id: int, advice_id: int) -> Notification | None:
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.ADVICE,
            title="오늘의 조언이 생성되었습니다.",
            message="오늘 입력한 건강 데이터를 바탕으로 맞춤 조언을 확인해 보세요.",
            link_url=f"/advices/today?advice_id={advice_id}",
        )

    async def notify_challenge_checkin(
        self,
        user_id: int,
        challenge_title: str,
        completed: bool = False,
    ) -> Notification | None:
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.CHALLENGE,
            title="챌린지 완료!" if completed else "챌린지 체크인이 완료되었습니다.",
            message=(
                f"{challenge_title} 챌린지를 모두 완료했습니다."
                if completed
                else f"{challenge_title} 오늘 미션을 완료했습니다."
            ),
            link_url="/challenges/my",
        )

    async def notify_weekly_report_created(self, user_id: int, report_id: int) -> Notification | None:
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.REPORT,
            title="주간 건강 리포트가 생성되었습니다.",
            message="이번 주 건강 기록과 챌린지 실천 현황을 확인해 보세요.",
            link_url=f"/reports/detail?report_id={report_id}",
        )

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
        if not payload:
            return self._to_preference_response(preference)
        for field, value in payload.items():
            setattr(preference, field, value)
        await preference.save(update_fields=[*payload.keys(), "updated_at"])
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
    def _preference_allows(preference: NotificationPreference, notification_type: NotificationType) -> bool:
        if notification_type == NotificationType.PREDICTION:
            return preference.push_enabled and preference.prediction_result_enabled
        if notification_type == NotificationType.CHALLENGE:
            return preference.push_enabled and preference.challenge_mission_enabled
        if notification_type == NotificationType.ADVICE:
            return preference.push_enabled and preference.advice_update_enabled
        if notification_type == NotificationType.REPORT:
            return preference.weekly_report_enabled
        if notification_type == NotificationType.GENERAL:
            return preference.important_notice_enabled
        return True

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
