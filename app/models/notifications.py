from tortoise import fields, models


class Notification(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="notifications", on_delete=fields.CASCADE)
    notification_type = fields.CharField(max_length=20)
    title = fields.CharField(max_length=100)
    message = fields.CharField(max_length=500)
    link_url = fields.CharField(max_length=255, null=True)
    is_read = fields.BooleanField(default=False)
    read_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"


class NotificationPreference(models.Model):
    user = fields.OneToOneField(
        "models.User",
        related_name="notification_preference",
        primary_key=True,
        on_delete=fields.CASCADE,
    )
    push_enabled = fields.BooleanField(default=True)
    health_data_reminder_enabled = fields.BooleanField(default=True)
    challenge_mission_enabled = fields.BooleanField(default=True)
    prediction_result_enabled = fields.BooleanField(default=True)
    advice_update_enabled = fields.BooleanField(default=True)
    virtual_pet_enabled = fields.BooleanField(default=True)
    email_enabled = fields.BooleanField(default=False)
    weekly_report_enabled = fields.BooleanField(default=True)
    important_notice_enabled = fields.BooleanField(default=True)
    promotion_enabled = fields.BooleanField(default=False)
    quiet_start_time = fields.TimeField(default="09:00:00")
    quiet_end_time = fields.TimeField(default="21:00:00")
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notification_preferences"
