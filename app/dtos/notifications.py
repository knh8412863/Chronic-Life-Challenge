from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


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
