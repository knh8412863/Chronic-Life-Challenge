from enum import StrEnum

from tortoise import fields, models


class FoodAnalysisStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class FoodAnalysisResult(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="food_analysis_results", on_delete=fields.CASCADE)
    task_uuid = fields.CharField(max_length=36, unique=True)
    status = fields.CharEnumField(enum_type=FoodAnalysisStatus, default=FoodAnalysisStatus.SUCCESS)
    meal_date = fields.DateField(null=True)
    meal_type = fields.CharField(max_length=20, null=True)
    food_name = fields.CharField(max_length=100)
    amount = fields.CharField(max_length=50, null=True)
    calories = fields.IntField(null=True)
    carbs_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    protein_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    fat_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    sodium_mg = fields.DecimalField(max_digits=8, decimal_places=2, null=True)
    sugar_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    fiber_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    health_score = fields.IntField()
    risk_flags = fields.JSONField(default=list)
    advice_text = fields.CharField(max_length=500)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "food_analysis_results"
