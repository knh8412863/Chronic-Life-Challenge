from tortoise import fields, models


class LLMAdvice(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="llm_advices", on_delete=fields.CASCADE)
    advice_date = fields.DateField()
    context_snapshot = fields.JSONField()
    prompt_summary = fields.TextField(null=True)
    advice_text = fields.CharField(max_length=400)
    provider = fields.CharField(max_length=20)
    model_name = fields.CharField(max_length=50)
    input_tokens = fields.IntField(null=True)
    output_tokens = fields.IntField(null=True)
    cache_read_tokens = fields.IntField(null=True)
    trigger_type = fields.CharField(max_length=10)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "llm_advices"


class AdviceFeedback(models.Model):
    id = fields.BigIntField(primary_key=True)
    advice = fields.OneToOneField(
        "models.LLMAdvice",
        related_name="feedback",
        on_delete=fields.CASCADE,
    )
    user = fields.ForeignKeyField("models.User", related_name="advice_feedbacks", on_delete=fields.CASCADE)
    feedback_type = fields.CharField(max_length=15)
    comment = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "advice_feedbacks"
