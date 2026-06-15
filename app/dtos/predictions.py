from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator

ResponseData = TypeVar("ResponseData")


class DataResponse(BaseModel, Generic[ResponseData]):
    data: ResponseData


class InputMode(StrEnum):
    BASIC = "BASIC"
    DEEP = "DEEP"


class DiseaseCode(StrEnum):
    HYPERTENSION = "HYPERTENSION"
    DIABETES = "DIABETES"
    DYSLIPIDEMIA = "DYSLIPIDEMIA"
    CKD = "CKD"
    OTHER = "OTHER"


class MedicationCode(StrEnum):
    HYPERTENSION = "HYPERTENSION"
    DIABETES = "DIABETES"


class LastCheckupPeriod(StrEnum):
    UNDER_6_MONTHS = "UNDER_6_MONTHS"
    UNDER_1_YEAR = "UNDER_1_YEAR"
    OVER_1_YEAR = "OVER_1_YEAR"
    NEVER = "NEVER"


class PredictionFeedbackType(StrEnum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    UNSURE = "UNSURE"


class VitalMeasureType(StrEnum):
    BP_MORNING = "BP_MORNING"
    BP_LUNCH = "BP_LUNCH"
    BP_EVENING = "BP_EVENING"
    GLUCOSE_FASTING = "GLUCOSE_FASTING"
    GLUCOSE_POSTPRANDIAL = "GLUCOSE_POSTPRANDIAL"


class ExerciseType(StrEnum):
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    CYCLING = "CYCLING"
    SWIMMING = "SWIMMING"
    ETC = "ETC"


class MealType(StrEnum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACK = "SNACK"


class HealthSurveyCreateRequest(BaseModel):
    input_mode: InputMode = InputMode.DEEP
    birth_date: date
    height: Annotated[float, Field(ge=130, le=210)]
    weight: Annotated[float, Field(ge=30, le=200)]
    waist_circumference: Annotated[float | None, Field(default=None, ge=50, le=150)]
    diagnosed_diseases: set[DiseaseCode] = Field(default_factory=set)
    medications: set[MedicationCode] = Field(default_factory=set)
    last_checkup_period: LastCheckupPeriod | None = None
    sbp: Annotated[int | None, Field(default=None, ge=70, le=250)]
    dbp: Annotated[int | None, Field(default=None, ge=40, le=150)]
    glucose_fasting: Annotated[int | None, Field(default=None, ge=50, le=500)]
    fh_diabetes_father: bool = False
    fh_diabetes_mother: bool = False
    fh_diabetes_sibling: bool = False
    fh_hypertension_father: bool = False
    fh_hypertension_mother: bool = False
    fh_hypertension_sibling: bool = False
    family_history_ckd: bool = False
    smoking_status: Literal[0, 1, 2]
    alcohol_frequency: Literal[0, 1, 3]
    alcohol_amount: Annotated[int | None, Field(default=None, ge=1, le=5)]
    walking_days: Annotated[int | None, Field(default=None, ge=0, le=7)]
    sedentary_hours: Annotated[float | None, Field(default=None, ge=0, le=24)]
    exercise_frequency: Annotated[int, Field(ge=0, le=7)]
    physical_activity_min: Annotated[int | None, Field(default=None, ge=0, le=3000)]
    sleep_hours: Annotated[float | None, Field(default=None, ge=0, le=14)]
    stress_level: Annotated[int | None, Field(default=None, ge=1, le=5)]
    diet_score: Annotated[float | None, Field(default=None, ge=0, le=10)]

    @model_validator(mode="after")
    def validate_alcohol_amount(self) -> "HealthSurveyCreateRequest":
        if self.alcohol_frequency == 0 and self.alcohol_amount is not None:
            raise ValueError("alcohol_amount must be empty when alcohol_frequency is 0.")
        if self.alcohol_frequency != 0 and self.alcohol_amount is None:
            raise ValueError("alcohol_amount is required when alcohol_frequency is not 0.")
        return self


class HealthSurveyCreateResponse(BaseModel):
    health_input_id: int
    bmi: float
    input_mode: InputMode
    profile_age_snapshot: int
    profile_gender_snapshot: str
    created_at: datetime


class LipidObesityRecordCreateRequest(BaseModel):
    record_date: date
    total_cholesterol: Annotated[int | None, Field(default=None, ge=80, le=400)]
    hdl_cholesterol: Annotated[int | None, Field(default=None, ge=10, le=120)]
    ldl_cholesterol: Annotated[int | None, Field(default=None, ge=30, le=300)]
    triglycerides: Annotated[int | None, Field(default=None, ge=30, le=1000)]
    waist_circumference: Annotated[float | None, Field(default=None, ge=50, le=150)]
    height: Annotated[float | None, Field(default=None, ge=130, le=210)]
    weight: Annotated[float | None, Field(default=None, ge=30, le=200)]
    memo: Annotated[str | None, Field(default=None, max_length=255)]

    @model_validator(mode="after")
    def validate_any_measurement(self) -> "LipidObesityRecordCreateRequest":
        fields = [
            self.total_cholesterol,
            self.hdl_cholesterol,
            self.ldl_cholesterol,
            self.triglycerides,
            self.waist_circumference,
            self.height,
            self.weight,
        ]
        if all(value is None for value in fields):
            raise ValueError("At least one lipid or obesity measurement is required.")
        if (self.height is None) != (self.weight is None):
            raise ValueError("height and weight must be submitted together to update BMI.")
        return self


class LipidObesityRecordUpdateRequest(BaseModel):
    record_date: date | None = None
    total_cholesterol: Annotated[int | None, Field(default=None, ge=80, le=400)]
    hdl_cholesterol: Annotated[int | None, Field(default=None, ge=10, le=120)]
    ldl_cholesterol: Annotated[int | None, Field(default=None, ge=30, le=300)]
    triglycerides: Annotated[int | None, Field(default=None, ge=30, le=1000)]
    waist_circumference: Annotated[float | None, Field(default=None, ge=50, le=150)]
    height: Annotated[float | None, Field(default=None, ge=130, le=210)]
    weight: Annotated[float | None, Field(default=None, ge=30, le=200)]
    memo: Annotated[str | None, Field(default=None, max_length=255)] = None

    @model_validator(mode="after")
    def validate_height_weight_pair(self) -> "LipidObesityRecordUpdateRequest":
        if (self.height is None) != (self.weight is None):
            raise ValueError("height and weight must be submitted together to update BMI.")
        return self


class RenalRecordCreateRequest(BaseModel):
    record_date: date
    creatinine: Annotated[float | None, Field(default=None, ge=0.1, le=20)]
    egfr: Annotated[float | None, Field(default=None, ge=0, le=200)]
    bun: Annotated[float | None, Field(default=None, ge=0, le=200)]
    urine_protein_pos: bool | None = None
    memo: Annotated[str | None, Field(default=None, max_length=255)]

    @model_validator(mode="after")
    def validate_any_measurement(self) -> "RenalRecordCreateRequest":
        fields = [self.creatinine, self.egfr, self.bun, self.urine_protein_pos]
        if all(value is None for value in fields):
            raise ValueError("At least one renal measurement is required.")
        return self


class RenalRecordUpdateRequest(BaseModel):
    record_date: date | None = None
    creatinine: Annotated[float | None, Field(default=None, ge=0.1, le=20)]
    egfr: Annotated[float | None, Field(default=None, ge=0, le=200)]
    bun: Annotated[float | None, Field(default=None, ge=0, le=200)]
    urine_protein_pos: bool | None = None
    memo: Annotated[str | None, Field(default=None, max_length=255)] = None


class VitalRecordCreateRequest(BaseModel):
    measured_at: datetime
    measure_type: VitalMeasureType
    sbp: Annotated[int | None, Field(default=None, ge=70, le=250)]
    dbp: Annotated[int | None, Field(default=None, ge=40, le=150)]
    glucose: Annotated[int | None, Field(default=None, ge=40, le=500)]
    memo: Annotated[str | None, Field(default=None, max_length=255)]

    @model_validator(mode="after")
    def validate_measurement_values(self) -> "VitalRecordCreateRequest":
        if self.measure_type.value.startswith("BP_"):
            if self.sbp is None or self.dbp is None:
                raise ValueError("sbp and dbp are required for blood pressure records.")
            if self.glucose is not None:
                raise ValueError("glucose must be empty for blood pressure records.")
        if self.measure_type.value.startswith("GLUCOSE_"):
            if self.glucose is None:
                raise ValueError("glucose is required for glucose records.")
            if self.sbp is not None or self.dbp is not None:
                raise ValueError("sbp and dbp must be empty for glucose records.")
        return self


class VitalRecordUpdateRequest(BaseModel):
    measured_at: datetime | None = None
    sbp: Annotated[int | None, Field(default=None, ge=70, le=250)]
    dbp: Annotated[int | None, Field(default=None, ge=40, le=150)]
    glucose: Annotated[int | None, Field(default=None, ge=40, le=500)]
    memo: Annotated[str | None, Field(default=None, max_length=255)] = None


class ActivityLogCreateRequest(BaseModel):
    record_date: date
    steps: Annotated[int | None, Field(default=None, ge=0, le=100000)]
    exercise_minutes: Annotated[int | None, Field(default=None, ge=0, le=1440)]
    water_ml: Annotated[int | None, Field(default=None, ge=0, le=10000)]
    alcohol_frequency: Literal[0, 1, 3] | None = None
    alcohol_amount: Annotated[int | None, Field(default=None, ge=1, le=5)]
    walking_days: Annotated[int | None, Field(default=None, ge=0, le=7)]
    sedentary_hours: Annotated[float | None, Field(default=None, ge=0, le=24)]
    sleep_hours: Annotated[float | None, Field(default=None, ge=0, le=14)]
    stress_level: Annotated[int | None, Field(default=None, ge=1, le=5)]
    diet_score: Annotated[float | None, Field(default=None, ge=0, le=10)]
    memo: Annotated[str | None, Field(default=None, max_length=255)]

    @model_validator(mode="after")
    def validate_activity_values(self) -> "ActivityLogCreateRequest":
        fields = [
            self.alcohol_frequency,
            self.walking_days,
            self.steps,
            self.exercise_minutes,
            self.water_ml,
            self.sedentary_hours,
            self.sleep_hours,
            self.stress_level,
            self.diet_score,
        ]
        if all(value is None for value in fields) and self.memo is None:
            raise ValueError("At least one activity value is required.")
        if self.alcohol_frequency == 0 and self.alcohol_amount is not None:
            raise ValueError("alcohol_amount must be empty when alcohol_frequency is 0.")
        if self.alcohol_frequency in {1, 3} and self.alcohol_amount is None:
            raise ValueError("alcohol_amount is required when alcohol_frequency is not 0.")
        return self


class ActivityLogUpdateRequest(BaseModel):
    steps: Annotated[int | None, Field(default=None, ge=0, le=100000)]
    exercise_minutes: Annotated[int | None, Field(default=None, ge=0, le=1440)]
    water_ml: Annotated[int | None, Field(default=None, ge=0, le=10000)]
    alcohol_frequency: Literal[0, 1, 3] | None = None
    alcohol_amount: Annotated[int | None, Field(default=None, ge=1, le=5)]
    walking_days: Annotated[int | None, Field(default=None, ge=0, le=7)]
    sedentary_hours: Annotated[float | None, Field(default=None, ge=0, le=24)]
    sleep_hours: Annotated[float | None, Field(default=None, ge=0, le=14)]
    stress_level: Annotated[int | None, Field(default=None, ge=1, le=5)]
    diet_score: Annotated[float | None, Field(default=None, ge=0, le=10)]
    memo: Annotated[str | None, Field(default=None, max_length=255)] = None


class ChronicDiseaseGoalUpdateRequest(BaseModel):
    target_systolic_bp: Annotated[int | None, Field(default=None, ge=80, le=180)]
    target_diastolic_bp: Annotated[int | None, Field(default=None, ge=50, le=120)]
    target_fasting_glucose: Annotated[int | None, Field(default=None, ge=70, le=180)]
    target_postprandial_glucose: Annotated[int | None, Field(default=None, ge=70, le=250)]
    target_hba1c: Annotated[float | None, Field(default=None, ge=4.0, le=12.0)]
    target_ldl_cholesterol: Annotated[int | None, Field(default=None, ge=30, le=200)]
    target_hdl_cholesterol: Annotated[int | None, Field(default=None, ge=30, le=120)]
    target_triglycerides: Annotated[int | None, Field(default=None, ge=30, le=500)]
    target_bmi: Annotated[float | None, Field(default=None, ge=18.5, le=35)]
    target_weight_kg: Annotated[float | None, Field(default=None, ge=30, le=200)]
    target_egfr: Annotated[float | None, Field(default=None, ge=15, le=150)]


class LifestyleGoalUpdateRequest(BaseModel):
    target_steps: Annotated[int | None, Field(default=None, ge=1000, le=30000)]
    target_water_ml: Annotated[int | None, Field(default=None, ge=500, le=5000)]
    target_exercise_minutes: Annotated[int | None, Field(default=None, ge=0, le=300)]
    target_sleep_hours: Annotated[float | None, Field(default=None, ge=4, le=12)]
    target_diet_score: Annotated[float | None, Field(default=None, ge=0, le=10)]


class HealthGoalUpdateRequest(BaseModel):
    chronic_disease_goal: ChronicDiseaseGoalUpdateRequest | None = None
    lifestyle_goal: LifestyleGoalUpdateRequest | None = None


class ExerciseLogCreateRequest(BaseModel):
    exercise_date: date
    exercise_type: ExerciseType
    duration_minutes: Annotated[int, Field(ge=1, le=1440)]
    calories_burned: Annotated[int | None, Field(default=None, ge=0, le=5000)]
    memo: Annotated[str | None, Field(default=None, max_length=255)]


class ExerciseLogUpdateRequest(BaseModel):
    exercise_date: date | None = None
    exercise_type: ExerciseType | None = None
    duration_minutes: Annotated[int | None, Field(default=None, ge=1, le=1440)]
    calories_burned: Annotated[int | None, Field(default=None, ge=0, le=5000)]
    memo: Annotated[str | None, Field(default=None, max_length=255)] = None


class MealLogCreateRequest(BaseModel):
    food_analysis_result_id: Annotated[int | None, Field(default=None, ge=1)]
    meal_date: date | None = None
    meal_type: MealType | None = None
    food_name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    amount: Annotated[str | None, Field(default=None, max_length=50)]
    calories: Annotated[int | None, Field(default=None, ge=0, le=10000)]
    carbs_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    protein_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    fat_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    sodium_mg: Annotated[float | None, Field(default=None, ge=0, le=100000)]
    sugar_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    fiber_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    memo: Annotated[str | None, Field(default=None, max_length=255)]

    @model_validator(mode="after")
    def validate_manual_required_fields(self) -> "MealLogCreateRequest":
        if self.food_analysis_result_id is not None:
            return self
        if self.meal_date is None or self.meal_type is None or self.food_name is None:
            raise ValueError("meal_date, meal_type, and food_name are required for manual meal logs.")
        return self


class MealLogUpdateRequest(BaseModel):
    food_analysis_result_id: Annotated[int | None, Field(default=None, ge=1)]
    meal_date: date | None = None
    meal_type: MealType | None = None
    food_name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    amount: Annotated[str | None, Field(default=None, max_length=50)]
    calories: Annotated[int | None, Field(default=None, ge=0, le=10000)]
    carbs_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    protein_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    fat_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    sodium_mg: Annotated[float | None, Field(default=None, ge=0, le=100000)]
    sugar_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    fiber_g: Annotated[float | None, Field(default=None, ge=0, le=1000)]
    memo: Annotated[str | None, Field(default=None, max_length=255)]


class OptionalRecordCreateResponse(BaseModel):
    record_id: int
    bmi: float | None = None
    created_at: datetime


class MealLogCreateResponse(BaseModel):
    meal_log_id: int
    meal_date: date
    created_at: datetime


class HealthSurveyRecordResponse(BaseModel):
    health_input_id: int
    input_mode: str
    age: int
    gender: str
    height: float
    weight: float
    bmi: float
    waist_circumference: float | None = None
    sbp: int | None = None
    dbp: int | None = None
    glucose_fasting: int | None = None
    diagnosed_diseases: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    last_checkup_period: str | None = None
    fh_diabetes_father: bool
    fh_diabetes_mother: bool
    fh_diabetes_sibling: bool
    fh_hypertension_father: bool
    fh_hypertension_mother: bool
    fh_hypertension_sibling: bool
    family_history_ckd: bool
    smoking_status: int
    alcohol_frequency: int
    alcohol_amount: int | None = None
    walking_days: int | None = None
    sedentary_hours: float | None = None
    exercise_frequency: int
    physical_activity_min: int | None = None
    sleep_hours: float | None = None
    stress_level: int | None = None
    diet_score: float | None = None
    created_at: datetime


class LipidObesityRecordResponse(BaseModel):
    record_id: int
    record_date: date
    total_cholesterol: int | None = None
    hdl_cholesterol: int | None = None
    ldl_cholesterol: int | None = None
    triglycerides: int | None = None
    height: float | None = None
    weight: float | None = None
    bmi: float | None = None
    waist_circumference: float | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime


class RenalRecordResponse(BaseModel):
    record_id: int
    record_date: date
    creatinine: float | None = None
    egfr: float | None = None
    bun: float | None = None
    urine_protein_pos: bool | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime


class VitalRecordResponse(BaseModel):
    record_id: int
    record_date: date
    measured_at: datetime
    measure_type: VitalMeasureType
    sbp: int | None = None
    dbp: int | None = None
    glucose: int | None = None
    memo: str | None = None
    is_critical: bool
    status_label: Literal["NORMAL", "CRITICAL"]
    created_at: datetime
    updated_at: datetime


class VitalRecordSummaryResponse(BaseModel):
    avg_sbp: float | None = None
    avg_dbp: float | None = None
    avg_glucose: float | None = None
    critical_count: int


class VitalRecordListResponse(BaseModel):
    summary: VitalRecordSummaryResponse
    total: int
    items: list[VitalRecordResponse]


class VitalTrendResponse(BaseModel):
    avg_sbp: float | None = None
    avg_dbp: float | None = None
    avg_glucose: float | None = None
    recent_7_days: list[VitalRecordResponse]


class VitalRecordDetailResponse(BaseModel):
    record: VitalRecordResponse
    trend: VitalTrendResponse


class ActivityLogResponse(BaseModel):
    activity_log_id: int
    record_date: date
    steps: int | None = None
    exercise_minutes: int | None = None
    water_ml: int | None = None
    alcohol_frequency: int | None = None
    alcohol_amount: int | None = None
    walking_days: int | None = None
    sedentary_hours: float | None = None
    sleep_hours: float | None = None
    stress_level: int | None = None
    diet_score: float | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime


class ActivityLogSummaryResponse(BaseModel):
    avg_walking_days: float | None = None
    avg_sedentary_hours: float | None = None
    avg_sleep_hours: float | None = None
    avg_stress_level: float | None = None
    avg_diet_score: float | None = None
    logged_days: int


class ActivityLogListResponse(BaseModel):
    summary: ActivityLogSummaryResponse
    total: int
    items: list[ActivityLogResponse]


class ChronicDiseaseGoalResponse(BaseModel):
    target_systolic_bp: int | None = None
    target_diastolic_bp: int | None = None
    target_fasting_glucose: int | None = None
    target_postprandial_glucose: int | None = None
    target_hba1c: float | None = None
    target_ldl_cholesterol: int | None = None
    target_hdl_cholesterol: int | None = None
    target_triglycerides: int | None = None
    target_bmi: float | None = None
    target_weight_kg: float | None = None
    target_egfr: float | None = None
    updated_at: datetime


class LifestyleGoalResponse(BaseModel):
    target_steps: int
    target_water_ml: int
    target_exercise_minutes: int
    target_sleep_hours: float | None = None
    target_diet_score: float | None = None
    updated_at: datetime


class HealthGoalResponse(BaseModel):
    chronic_disease_goal: ChronicDiseaseGoalResponse
    lifestyle_goal: LifestyleGoalResponse


class ExerciseLogResponse(BaseModel):
    exercise_log_id: int
    exercise_date: date
    exercise_type: ExerciseType
    duration_minutes: int
    calories_burned: int | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime


class ExerciseLogSummaryResponse(BaseModel):
    total_duration_minutes: int
    total_calories_burned: int
    logged_count: int


class ExerciseLogListResponse(BaseModel):
    summary: ExerciseLogSummaryResponse
    total: int
    items: list[ExerciseLogResponse]


class MealLogResponse(BaseModel):
    meal_log_id: int
    food_analysis_result_id: int | None = None
    meal_date: date
    meal_type: MealType
    food_name: str
    amount: str | None = None
    calories: int | None = None
    carbs_g: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    fiber_g: float | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime


class MealDailySummaryResponse(BaseModel):
    meal_date: date
    meal_count: int
    total_calories: int
    total_sodium_mg: float
    total_sugar_g: float
    total_fiber_g: float


class MealLogListResponse(BaseModel):
    daily_summary: list[MealDailySummaryResponse]
    total: int
    items: list[MealLogResponse]


class HealthGoalProgressResponse(BaseModel):
    metric: Literal["EXERCISE_MINUTES", "SLEEP_HOURS", "DIET_SCORE"]
    current_value: float | None = None
    target_value: float | None = None
    unit: str
    progress_rate: float | None = None
    status: Literal["ACHIEVED", "IN_PROGRESS", "UNAVAILABLE"]


class HealthStatisticsResponse(BaseModel):
    period_start: date
    period_end: date
    vital_summary: VitalRecordSummaryResponse
    latest_vital_record: VitalRecordResponse | None = None
    activity_summary: ActivityLogSummaryResponse
    latest_activity_log: ActivityLogResponse | None = None
    exercise_summary: ExerciseLogSummaryResponse
    latest_exercise_log: ExerciseLogResponse | None = None
    goal_progress: list[HealthGoalProgressResponse]


class MetricAssessmentItemResponse(BaseModel):
    status: Literal["NORMAL", "CAUTION", "HIGH", "UNAVAILABLE"]
    reasons: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class MetricAssessmentResponse(BaseModel):
    dyslipidemia: MetricAssessmentItemResponse
    obesity: MetricAssessmentItemResponse


class PredictionTaskCreateRequest(BaseModel):
    health_input_id: int | None = None
    prediction_mode: Literal["SCREENING"] = "SCREENING"


class PredictionTaskCreateResponse(BaseModel):
    task_uuid: str
    status: str
    prediction_mode: str


class PredictionTaskStatusResponse(BaseModel):
    task_uuid: str
    status: str
    progress_percent: int
    current_step: str
    result_id: int | None = None
    error_message: str | None = None


class DiseaseRiskResponse(BaseModel):
    probability: float
    risk_score: float
    threshold: float
    is_at_risk: bool
    risk_level: str
    message: str
    risk_factors: list[str] = Field(default_factory=list)


class InputCompletenessResponse(BaseModel):
    used_default_values: bool
    missing_fields: list[str]
    message: str


class PredictionResultResponse(BaseModel):
    result_id: int
    prediction_mode: str
    created_at: datetime
    disease_risks: dict[str, DiseaseRiskResponse]
    input_completeness: InputCompletenessResponse
    disclaimer: str


class PredictionResultListItemResponse(BaseModel):
    result_id: int
    prediction_mode: str
    created_at: datetime
    overall_risk_level: str
    highest_risk_disease: str | None = None
    highest_risk_probability: float | None = None
    highest_risk_score: float | None = None
    disease_risks: dict[str, DiseaseRiskResponse]
    input_completeness: InputCompletenessResponse
    feedback_submitted: bool


class PredictionResultListResponse(BaseModel):
    total: int
    items: list[PredictionResultListItemResponse]


class PredictionFeedbackCreateRequest(BaseModel):
    feedback_type: PredictionFeedbackType
    actual_diagnosis: dict[str, bool] | None = None
    comment: Annotated[str | None, Field(default=None, max_length=500)]


class PredictionFeedbackCreateResponse(BaseModel):
    feedback_id: int
    prediction_result_id: int
    feedback_type: PredictionFeedbackType
    created_at: datetime
