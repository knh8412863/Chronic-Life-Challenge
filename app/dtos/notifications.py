from datetime import datetime, time
from enum import StrEnum

from pydantic import BaseModel, model_validator


class NotificationType(StrEnum):
    GENERAL = "GENERAL"
    PREDICTION = "PREDICTION"
    CHALLENGE = "CHALLENGE"
    ADVICE = "ADVICE"
    REPORT = "REPORT"


class NotificationResponse(BaseModel):
    notification_id: int
    notification_type: NotificationType
    title: str
    message: str
    link_url: str | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationMarkReadResponse(BaseModel):
    notification_id: int
    is_read: bool
    read_at: datetime


class NotificationMarkAllReadResponse(BaseModel):
    updated_count: int
    unread_count: int = 0


class NotificationPreferenceResponse(BaseModel):
    push_enabled: bool
    health_data_reminder_enabled: bool
    challenge_mission_enabled: bool
    prediction_result_enabled: bool
    advice_update_enabled: bool
    virtual_pet_enabled: bool
    email_enabled: bool
    weekly_report_enabled: bool
    important_notice_enabled: bool
    promotion_enabled: bool
    quiet_start_time: time
    quiet_end_time: time


class NotificationPreferenceUpdateRequest(BaseModel):
    push_enabled: bool | None = None
    health_data_reminder_enabled: bool | None = None
    challenge_mission_enabled: bool | None = None
    prediction_result_enabled: bool | None = None
    advice_update_enabled: bool | None = None
    virtual_pet_enabled: bool | None = None
    email_enabled: bool | None = None
    weekly_report_enabled: bool | None = None
    important_notice_enabled: bool | None = None
    promotion_enabled: bool | None = None
    quiet_start_time: time | None = None
    quiet_end_time: time | None = None

    @model_validator(mode="after")
    def validate_quiet_times(self):
        if self.quiet_start_time and self.quiet_end_time and self.quiet_start_time == self.quiet_end_time:
            raise ValueError("알림 시작 시간과 종료 시간은 달라야 합니다.")
        return self
