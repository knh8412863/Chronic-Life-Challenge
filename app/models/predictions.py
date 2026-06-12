from enum import StrEnum

from tortoise import fields, models

from app.models.users import Gender


class PredictionMode(StrEnum):
    SCREENING = "SCREENING"


class PredictionStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class UserProfile(models.Model):
    user = fields.OneToOneField("models.User", related_name="profile", primary_key=True, on_delete=fields.CASCADE)
    birth_date = fields.DateField()
    gender = fields.CharEnumField(enum_type=Gender)
    height_cm = fields.DecimalField(max_digits=5, decimal_places=2)
    weight_kg = fields.DecimalField(max_digits=5, decimal_places=2)
    bmi = fields.DecimalField(max_digits=5, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_profiles"


class UserChronicDiseaseGoal(models.Model):
    user = fields.OneToOneField(
        "models.User", related_name="chronic_disease_goal", primary_key=True, on_delete=fields.CASCADE
    )
    target_systolic_bp = fields.IntField(null=True)
    target_diastolic_bp = fields.IntField(null=True)
    target_fasting_glucose = fields.IntField(null=True)
    target_postprandial_glucose = fields.IntField(null=True)
    target_hba1c = fields.DecimalField(max_digits=4, decimal_places=2, null=True)
    target_ldl_cholesterol = fields.IntField(null=True)
    target_hdl_cholesterol = fields.IntField(null=True)
    target_triglycerides = fields.IntField(null=True)
    target_bmi = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    target_weight_kg = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    target_egfr = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_chronic_disease_goals"


class UserLifestyleGoal(models.Model):
    user = fields.OneToOneField(
        "models.User", related_name="lifestyle_goal", primary_key=True, on_delete=fields.CASCADE
    )
    target_steps = fields.IntField(default=10000)
    target_water_ml = fields.IntField(default=2000)
    target_exercise_minutes = fields.IntField(default=30)
    target_sleep_hours = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    target_diet_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_lifestyle_goals"


class ChronicHealthInput(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="chronic_health_inputs", on_delete=fields.CASCADE)
    age = fields.IntField()
    gender = fields.CharEnumField(enum_type=Gender)
    height = fields.DecimalField(max_digits=5, decimal_places=2)
    weight = fields.DecimalField(max_digits=5, decimal_places=2)
    bmi = fields.DecimalField(max_digits=5, decimal_places=2)
    waist_circumference = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    sbp = fields.IntField(null=True)
    dbp = fields.IntField(null=True)
    glucose_fasting = fields.IntField(null=True)
    diagnosed_diseases = fields.JSONField(default=list)
    medications = fields.JSONField(default=list)
    last_checkup_period = fields.CharField(max_length=20, null=True)
    fh_diabetes_father = fields.BooleanField(default=False)
    fh_diabetes_mother = fields.BooleanField(default=False)
    fh_diabetes_sibling = fields.BooleanField(default=False)
    fh_hypertension_father = fields.BooleanField(default=False)
    fh_hypertension_mother = fields.BooleanField(default=False)
    fh_hypertension_sibling = fields.BooleanField(default=False)
    family_history_ckd = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chronic_health_inputs"


class LifestyleInput(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="lifestyle_inputs", on_delete=fields.CASCADE)
    smoking_status = fields.IntField()
    alcohol_frequency = fields.IntField()
    alcohol_amount = fields.IntField(null=True)
    walking_days = fields.IntField(null=True)
    sedentary_hours = fields.DecimalField(max_digits=4, decimal_places=1, null=True)
    exercise_frequency = fields.IntField()
    physical_activity_min = fields.IntField(null=True)
    sleep_hours = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    stress_level = fields.IntField(null=True)
    diet_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "lifestyle_inputs"


class LipidObesityRecord(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="lipid_obesity_records", on_delete=fields.CASCADE)
    record_date = fields.DateField()
    total_cholesterol = fields.IntField(null=True)
    hdl_cholesterol = fields.IntField(null=True)
    ldl_cholesterol = fields.IntField(null=True)
    triglycerides = fields.IntField(null=True)
    height_cm = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    weight_kg = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    bmi = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    waist_circumference = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    memo = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "lipid_obesity_records"


class RenalRecord(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="renal_records", on_delete=fields.CASCADE)
    record_date = fields.DateField()
    creatinine = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    egfr = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    bun = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    urine_protein_pos = fields.BooleanField(null=True)
    memo = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "renal_records"


class VitalRecord(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="vital_records", on_delete=fields.CASCADE)
    record_date = fields.DateField()
    measured_at = fields.DatetimeField()
    measure_type = fields.CharField(max_length=25)
    sbp = fields.IntField(null=True)
    dbp = fields.IntField(null=True)
    glucose = fields.IntField(null=True)
    memo = fields.CharField(max_length=255, null=True)
    is_critical = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "vital_records"


class ActivityLog(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="activity_logs", on_delete=fields.CASCADE)
    record_date = fields.DateField()
    alcohol_frequency = fields.IntField(null=True)
    alcohol_amount = fields.IntField(null=True)
    walking_days = fields.IntField(null=True)
    steps = fields.IntField(null=True)
    exercise_minutes = fields.IntField(null=True)
    water_ml = fields.IntField(null=True)
    sedentary_hours = fields.DecimalField(max_digits=4, decimal_places=1, null=True)
    sleep_hours = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    stress_level = fields.IntField(null=True)
    diet_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True)
    memo = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "activity_logs"


class ExerciseLog(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="exercise_logs", on_delete=fields.CASCADE)
    exercise_date = fields.DateField()
    exercise_type = fields.CharField(max_length=50)
    duration_minutes = fields.IntField()
    calories_burned = fields.IntField(null=True)
    memo = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "exercise_logs"


class MealLog(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="meal_logs", on_delete=fields.CASCADE)
    food_analysis_result = fields.ForeignKeyField(
        "models.FoodAnalysisResult",
        related_name="meal_logs",
        null=True,
        on_delete=fields.SET_NULL,
    )
    meal_date = fields.DateField()
    meal_type = fields.CharField(max_length=20)
    food_name = fields.CharField(max_length=100)
    amount = fields.CharField(max_length=50, null=True)
    calories = fields.IntField(null=True)
    carbs_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    protein_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    fat_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    sodium_mg = fields.DecimalField(max_digits=8, decimal_places=2, null=True)
    sugar_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    fiber_g = fields.DecimalField(max_digits=6, decimal_places=2, null=True)
    memo = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "meal_logs"


class PredictionInputSnapshot(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="prediction_input_snapshots", on_delete=fields.CASCADE)
    input_mode = fields.CharField(max_length=10)
    chronic_health_input = fields.ForeignKeyField("models.ChronicHealthInput", related_name="snapshots")
    lifestyle_input = fields.ForeignKeyField("models.LifestyleInput", related_name="snapshots")
    lipid_obesity_record = fields.ForeignKeyField("models.LipidObesityRecord", null=True, related_name="snapshots")
    renal_record = fields.ForeignKeyField("models.RenalRecord", null=True, related_name="snapshots")
    used_default_values = fields.BooleanField(default=False)
    missing_fields = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prediction_input_snapshots"


class ModelVersion(models.Model):
    id = fields.BigIntField(primary_key=True)
    version = fields.CharField(max_length=20)
    disease_code = fields.CharField(max_length=30)
    model_task = fields.CharField(max_length=30, default="BINARY_CLASSIFICATION")
    threshold = fields.DecimalField(max_digits=6, decimal_places=5, null=True)
    is_active = fields.BooleanField(default=True)
    metadata = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "model_versions"
        unique_together = (("version", "disease_code", "model_task"),)
        indexes = (("disease_code", "is_active"),)


class PredictionTask(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="prediction_tasks", on_delete=fields.CASCADE)
    task_uuid = fields.CharField(max_length=36, unique=True)
    input_snapshot = fields.ForeignKeyField("models.PredictionInputSnapshot", related_name="tasks")
    prediction_mode = fields.CharEnumField(enum_type=PredictionMode, default=PredictionMode.SCREENING)
    status = fields.CharEnumField(enum_type=PredictionStatus, default=PredictionStatus.PENDING)
    progress_percent = fields.IntField(default=0)
    current_step = fields.CharField(max_length=100, null=True)
    requested_at = fields.DatetimeField(auto_now_add=True)
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    error_message = fields.CharField(max_length=500, null=True)

    class Meta:
        table = "prediction_tasks"


class PredictionResult(models.Model):
    id = fields.BigIntField(primary_key=True)
    task = fields.OneToOneField("models.PredictionTask", related_name="result", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="prediction_results", on_delete=fields.CASCADE)
    overall_risk_level = fields.CharField(max_length=10)
    lifestyle_priority = fields.JSONField(default=list)
    input_completeness = fields.JSONField(default=dict)
    inference_ms = fields.IntField(null=True)
    disclaimer = fields.CharField(max_length=500)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prediction_results"


class PredictionResultItem(models.Model):
    id = fields.BigIntField(primary_key=True)
    result = fields.ForeignKeyField("models.PredictionResult", related_name="items", on_delete=fields.CASCADE)
    disease_code = fields.CharField(max_length=30)
    model_version = fields.CharField(max_length=20, default="V8")
    model_version_ref = fields.ForeignKeyField(
        "models.ModelVersion",
        related_name="prediction_result_items",
        null=True,
        on_delete=fields.SET_NULL,
    )
    probability = fields.DecimalField(max_digits=7, decimal_places=6)
    threshold = fields.DecimalField(max_digits=6, decimal_places=5)
    threshold_profile = fields.CharField(max_length=15, default=PredictionMode.SCREENING.value)
    is_at_risk = fields.BooleanField()
    risk_level = fields.CharField(max_length=10)
    message = fields.CharField(max_length=500)
    risk_factors = fields.JSONField(default=list)

    class Meta:
        table = "prediction_result_items"
        unique_together = (("result", "disease_code"),)


class PredictionFeedback(models.Model):
    id = fields.BigIntField(primary_key=True)
    prediction_result = fields.OneToOneField(
        "models.PredictionResult",
        related_name="feedback",
        on_delete=fields.CASCADE,
    )
    user = fields.ForeignKeyField("models.User", related_name="prediction_feedbacks", on_delete=fields.CASCADE)
    feedback_type = fields.CharField(max_length=15)
    actual_diagnosis = fields.JSONField(null=True)
    comment = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prediction_feedback"
