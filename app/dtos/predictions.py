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


class OptionalRecordCreateResponse(BaseModel):
    record_id: int
    bmi: float | None = None
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


class MetricAssessmentItemResponse(BaseModel):
    status: Literal["NORMAL", "CAUTION", "HIGH", "UNAVAILABLE"]
    reasons: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class MetricAssessmentResponse(BaseModel):
    dyslipidemia: MetricAssessmentItemResponse
    obesity: MetricAssessmentItemResponse


class PredictionTaskCreateRequest(BaseModel):
    health_input_id: int
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
    disease_risks: dict[str, DiseaseRiskResponse]
    input_completeness: InputCompletenessResponse
    disclaimer: str


class PredictionFeedbackCreateRequest(BaseModel):
    feedback_type: PredictionFeedbackType
    actual_diagnosis: dict[str, bool] | None = None
    comment: Annotated[str | None, Field(default=None, max_length=500)]


class PredictionFeedbackCreateResponse(BaseModel):
    feedback_id: int
    prediction_result_id: int
    feedback_type: PredictionFeedbackType
    created_at: datetime
