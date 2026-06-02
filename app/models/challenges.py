from tortoise import fields, models


class Challenge(models.Model):
    id = fields.BigIntField(primary_key=True)
    title = fields.CharField(max_length=100)
    description = fields.CharField(max_length=500)
    category = fields.CharField(max_length=30)
    target_metric = fields.CharField(max_length=30)
    goal_value = fields.IntField()
    duration_days = fields.IntField()
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "challenges"


class ChallengeParticipation(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="challenge_participations", on_delete=fields.CASCADE)
    challenge = fields.ForeignKeyField("models.Challenge", related_name="participations", on_delete=fields.CASCADE)
    start_date = fields.DateField()
    end_date = fields.DateField()
    status = fields.CharField(max_length=15)
    progress_count = fields.IntField(default=0)
    completed_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "challenge_participations"


class ChallengeCheckin(models.Model):
    id = fields.BigIntField(primary_key=True)
    participation = fields.ForeignKeyField(
        "models.ChallengeParticipation",
        related_name="checkins",
        on_delete=fields.CASCADE,
    )
    user = fields.ForeignKeyField("models.User", related_name="challenge_checkins", on_delete=fields.CASCADE)
    checkin_date = fields.DateField()
    note = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "challenge_checkins"
        unique_together = (("participation", "checkin_date"),)
