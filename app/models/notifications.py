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
