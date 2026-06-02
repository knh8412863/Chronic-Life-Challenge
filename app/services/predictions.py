import asyncio
import time
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.core import config
from app.dtos.predictions import (
    ActivityLogCreateRequest,
    ActivityLogListResponse,
    ActivityLogResponse,
    ActivityLogSummaryResponse,
    ActivityLogUpdateRequest,
    ChronicDiseaseGoalResponse,
    ExerciseLogCreateRequest,
    ExerciseLogListResponse,
    ExerciseLogResponse,
    ExerciseLogSummaryResponse,
    ExerciseLogUpdateRequest,
    ExerciseType,
    HealthGoalProgressResponse,
    HealthGoalResponse,
    HealthGoalUpdateRequest,
    HealthStatisticsResponse,
    HealthSurveyCreateRequest,
    HealthSurveyCreateResponse,
    HealthSurveyRecordResponse,
    InputCompletenessResponse,
    LifestyleGoalResponse,
    LipidObesityRecordCreateRequest,
    LipidObesityRecordResponse,
    MealDailySummaryResponse,
    MealLogCreateRequest,
    MealLogCreateResponse,
    MealLogListResponse,
    MealLogResponse,
    MealLogUpdateRequest,
    MealType,
    MetricAssessmentItemResponse,
    MetricAssessmentResponse,
    OptionalRecordCreateResponse,
    PredictionFeedbackCreateRequest,
    PredictionFeedbackCreateResponse,
    PredictionResultResponse,
    PredictionTaskCreateRequest,
    PredictionTaskCreateResponse,
    PredictionTaskStatusResponse,
    RenalRecordCreateRequest,
    RenalRecordResponse,
    VitalMeasureType,
    VitalRecordCreateRequest,
    VitalRecordDetailResponse,
    VitalRecordListResponse,
    VitalRecordResponse,
    VitalRecordSummaryResponse,
    VitalRecordUpdateRequest,
    VitalTrendResponse,
)
from app.models.predictions import (
    ActivityLog,
    ChronicHealthInput,
    ExerciseLog,
    LifestyleInput,
    LipidObesityRecord,
    MealLog,
    PredictionFeedback,
    PredictionInputSnapshot,
    PredictionMode,
    PredictionResult,
    PredictionResultItem,
    PredictionStatus,
    PredictionTask,
    RenalRecord,
    UserChronicDiseaseGoal,
    UserLifestyleGoal,
    UserProfile,
    VitalRecord,
)
from app.models.users import Gender, User

DISCLAIMER = "본 결과는 의료 진단이 아닌 참고 지표입니다. 증상이나 우려가 있다면 전문의와 상담해 주세요."
MODELS_DIR = Path(__file__).resolve().parents[2] / "ai_worker" / "models"

DISEASE_MAPPINGS = {
    "diabetes": ("DIABETES", "당뇨"),
    "hypertension": ("HYPERTENSION", "고혈압"),
    "kidney": ("CKD", "만성신장질환"),
}

DYSLIPIDEMIA_FIELDS = ["total_cholesterol", "hdl_cholesterol", "ldl_cholesterol", "triglycerides"]
DYSLIPIDEMIA_UPPER_RULES = {
    "total_cholesterol": (200, 240, "총콜레스테롤"),
    "ldl_cholesterol": (130, 160, "LDL 콜레스테롤"),
    "triglycerides": (150, 200, "중성지방"),
}
PREDICTION_PROGRESS = {
    PredictionStatus.PENDING: (0, "예측 요청 접수"),
    PredictionStatus.RUNNING: (60, "AI 모델 실행 중"),
    PredictionStatus.SUCCESS: (100, "예측 완료"),
    PredictionStatus.FAILED: (100, "예측 실패"),
}
DEFAULT_LIFESTYLE_GOAL = {
    "target_steps": 10000,
    "target_water_ml": 2000,
    "target_exercise_minutes": 30,
    "target_sleep_hours": None,
    "target_diet_score": None,
}


def _calculate_age(birth_date: date, today: date | None = None) -> int:
    current = today or date.today()
    return current.year - birth_date.year - ((current.month, current.day) < (birth_date.month, birth_date.day))


def _calculate_bmi(height_cm: float, weight_kg: float) -> float:
    return round(weight_kg / ((height_cm / 100) ** 2), 2)


def _gender_label(gender: Gender) -> str:
    return "M" if gender == Gender.MALE else "F"


class HealthInputService:
    async def create_survey(self, user: User, data: HealthSurveyCreateRequest) -> HealthSurveyCreateResponse:
        bmi = _calculate_bmi(data.height, data.weight)
        age = _calculate_age(data.birth_date)
        if age < 19 or age > 89:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="지원 연령은 19~89세입니다.")

        async with in_transaction():
            await UserProfile.update_or_create(
                defaults={
                    "birth_date": data.birth_date,
                    "gender": user.gender,
                    "height_cm": Decimal(str(data.height)),
                    "weight_kg": Decimal(str(data.weight)),
                    "bmi": Decimal(str(bmi)),
                },
                user_id=user.id,
            )
            health = await ChronicHealthInput.create(
                user=user,
                age=age,
                gender=user.gender,
                height=Decimal(str(data.height)),
                weight=Decimal(str(data.weight)),
                bmi=Decimal(str(bmi)),
                waist_circumference=(
                    Decimal(str(data.waist_circumference)) if data.waist_circumference is not None else None
                ),
                sbp=data.sbp,
                dbp=data.dbp,
                glucose_fasting=data.glucose_fasting,
                diagnosed_diseases=sorted(item.value for item in data.diagnosed_diseases),
                medications=sorted(item.value for item in data.medications),
                last_checkup_period=data.last_checkup_period.value if data.last_checkup_period else None,
                fh_diabetes_father=data.fh_diabetes_father,
                fh_diabetes_mother=data.fh_diabetes_mother,
                fh_diabetes_sibling=data.fh_diabetes_sibling,
                fh_hypertension_father=data.fh_hypertension_father,
                fh_hypertension_mother=data.fh_hypertension_mother,
                fh_hypertension_sibling=data.fh_hypertension_sibling,
                family_history_ckd=data.family_history_ckd,
            )
            lifestyle = await LifestyleInput.create(
                user=user,
                smoking_status=data.smoking_status,
                alcohol_frequency=data.alcohol_frequency,
                alcohol_amount=data.alcohol_amount,
                walking_days=data.walking_days,
                sedentary_hours=data.sedentary_hours,
                exercise_frequency=data.exercise_frequency,
                physical_activity_min=data.physical_activity_min,
                sleep_hours=data.sleep_hours,
                stress_level=data.stress_level,
                diet_score=data.diet_score,
            )
            snapshot = await PredictionInputSnapshot.create(
                user=user,
                input_mode=data.input_mode.value,
                chronic_health_input=health,
                lifestyle_input=lifestyle,
            )

        return HealthSurveyCreateResponse(
            health_input_id=snapshot.id,
            bmi=bmi,
            input_mode=data.input_mode,
            profile_age_snapshot=age,
            profile_gender_snapshot=_gender_label(user.gender),
            created_at=snapshot.created_at,
        )

    async def create_lipid_obesity_record(
        self, user: User, data: LipidObesityRecordCreateRequest
    ) -> OptionalRecordCreateResponse:
        bmi = _calculate_bmi(data.height, data.weight) if data.height is not None and data.weight is not None else None
        record = await LipidObesityRecord.create(
            user=user,
            record_date=data.record_date,
            total_cholesterol=data.total_cholesterol,
            hdl_cholesterol=data.hdl_cholesterol,
            ldl_cholesterol=data.ldl_cholesterol,
            triglycerides=data.triglycerides,
            height_cm=data.height,
            weight_kg=data.weight,
            bmi=bmi,
            waist_circumference=data.waist_circumference,
            memo=data.memo,
        )
        if bmi is not None:
            await UserProfile.filter(user_id=user.id).update(
                height_cm=data.height,
                weight_kg=data.weight,
                bmi=bmi,
            )
        return OptionalRecordCreateResponse(record_id=record.id, bmi=bmi, created_at=record.created_at)

    async def create_renal_record(self, user: User, data: RenalRecordCreateRequest) -> OptionalRecordCreateResponse:
        record = await RenalRecord.create(user=user, **data.model_dump())
        return OptionalRecordCreateResponse(record_id=record.id, created_at=record.created_at)

    async def get_metric_assessments(self, user: User) -> MetricAssessmentResponse:
        profile = await UserProfile.get_or_none(user_id=user.id)
        latest_health = await ChronicHealthInput.filter(user_id=user.id).order_by("-created_at").first()
        latest_lipid = await LipidObesityRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()

        return MetricAssessmentResponse(
            dyslipidemia=self._assess_dyslipidemia(user, latest_lipid),
            obesity=self._assess_obesity(user, profile, latest_health, latest_lipid),
        )

    async def get_health_surveys(self, user: User, limit: int = 20) -> list[HealthSurveyRecordResponse]:
        snapshots = (
            await PredictionInputSnapshot.filter(user_id=user.id)
            .order_by("-created_at")
            .limit(limit)
            .prefetch_related("chronic_health_input", "lifestyle_input")
        )
        return [self._to_health_survey_record(snapshot) for snapshot in snapshots]

    async def get_latest_health_survey(self, user: User) -> HealthSurveyRecordResponse:
        snapshot = (
            await PredictionInputSnapshot.filter(user_id=user.id)
            .order_by("-created_at")
            .prefetch_related("chronic_health_input", "lifestyle_input")
            .first()
        )
        if snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="건강 설문 입력을 찾을 수 없습니다.")
        return self._to_health_survey_record(snapshot)

    async def get_lipid_obesity_records(self, user: User, limit: int = 20) -> list[LipidObesityRecordResponse]:
        records = await LipidObesityRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").limit(limit)
        return [self._to_lipid_obesity_record(record) for record in records]

    async def get_lipid_obesity_record(self, user: User, record_id: int) -> LipidObesityRecordResponse:
        record = await LipidObesityRecord.get_or_none(id=record_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="지질·비만 기록을 찾을 수 없습니다.")
        return self._to_lipid_obesity_record(record)

    async def get_renal_records(self, user: User, limit: int = 20) -> list[RenalRecordResponse]:
        records = await RenalRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").limit(limit)
        return [self._to_renal_record(record) for record in records]

    async def get_renal_record(self, user: User, record_id: int) -> RenalRecordResponse:
        record = await RenalRecord.get_or_none(id=record_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="신장 기록을 찾을 수 없습니다.")
        return self._to_renal_record(record)

    async def create_vital_record(self, user: User, data: VitalRecordCreateRequest) -> OptionalRecordCreateResponse:
        is_critical = self._is_vital_critical(data.measure_type.value, data.sbp, data.dbp, data.glucose)
        record = await VitalRecord.create(
            user=user,
            record_date=data.measured_at.date(),
            measured_at=data.measured_at,
            measure_type=data.measure_type.value,
            sbp=data.sbp,
            dbp=data.dbp,
            glucose=data.glucose,
            memo=data.memo,
            is_critical=is_critical,
        )
        return OptionalRecordCreateResponse(record_id=record.id, created_at=record.created_at)

    async def get_vital_records(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
        measure_type: VitalMeasureType | None = None,
        limit: int = 100,
    ) -> VitalRecordListResponse:
        query = VitalRecord.filter(user_id=user.id)
        if from_date is not None:
            query = query.filter(record_date__gte=from_date)
        if to_date is not None:
            query = query.filter(record_date__lte=to_date)
        if measure_type is not None:
            query = query.filter(measure_type=measure_type.value)

        records = await query.order_by("-measured_at", "-id").limit(limit)
        items = [self._to_vital_record(record) for record in records]
        return VitalRecordListResponse(
            summary=self._build_vital_summary(records),
            total=len(items),
            items=items,
        )

    async def get_vital_record(self, user: User, record_id: int) -> VitalRecordDetailResponse:
        record = await VitalRecord.get_or_none(id=record_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="혈압·혈당 기록을 찾을 수 없습니다.")

        start_date = record.record_date - timedelta(days=6)
        trend_records = (
            await VitalRecord.filter(user_id=user.id, record_date__gte=start_date, record_date__lte=record.record_date)
            .order_by("record_date", "measured_at", "id")
            .limit(100)
        )
        return VitalRecordDetailResponse(
            record=self._to_vital_record(record),
            trend=VitalTrendResponse(
                **self._build_vital_summary(trend_records).model_dump(),
                recent_7_days=[self._to_vital_record(item) for item in trend_records],
            ),
        )

    async def update_vital_record(
        self,
        user: User,
        record_id: int,
        data: VitalRecordUpdateRequest,
    ) -> VitalRecordResponse:
        record = await VitalRecord.get_or_none(id=record_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="혈압·혈당 기록을 찾을 수 없습니다.")
        self._ensure_today_record(record.record_date)

        update_data = data.model_dump(exclude_unset=True)
        measured_at = update_data.get("measured_at", record.measured_at)
        if measured_at.date() != self._today():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="당일 기록만 수정할 수 있습니다.")

        sbp = update_data.get("sbp", record.sbp)
        dbp = update_data.get("dbp", record.dbp)
        glucose = update_data.get("glucose", record.glucose)
        self._validate_vital_values(record.measure_type, sbp, dbp, glucose)

        record.measured_at = measured_at
        record.record_date = measured_at.date()
        record.sbp = sbp
        record.dbp = dbp
        record.glucose = glucose
        if "memo" in update_data:
            record.memo = update_data["memo"]
        record.is_critical = self._is_vital_critical(record.measure_type, record.sbp, record.dbp, record.glucose)
        await record.save()
        return self._to_vital_record(record)

    async def delete_vital_record(self, user: User, record_id: int) -> None:
        record = await VitalRecord.get_or_none(id=record_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="혈압·혈당 기록을 찾을 수 없습니다.")
        self._ensure_today_record(record.record_date)
        await record.delete()

    async def create_activity_log(self, user: User, data: ActivityLogCreateRequest) -> OptionalRecordCreateResponse:
        exists = await ActivityLog.exists(user_id=user.id, record_date=data.record_date)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 날짜의 생활습관 기록입니다.")

        record = await ActivityLog.create(
            user=user,
            record_date=data.record_date,
            alcohol_frequency=data.alcohol_frequency,
            alcohol_amount=data.alcohol_amount,
            walking_days=data.walking_days,
            sedentary_hours=self._optional_decimal(data.sedentary_hours),
            sleep_hours=self._optional_decimal(data.sleep_hours),
            stress_level=data.stress_level,
            diet_score=self._optional_decimal(data.diet_score),
            memo=data.memo,
        )
        return OptionalRecordCreateResponse(record_id=record.id, created_at=record.created_at)

    async def get_activity_logs(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int = 100,
    ) -> ActivityLogListResponse:
        query = ActivityLog.filter(user_id=user.id)
        if from_date is not None:
            query = query.filter(record_date__gte=from_date)
        if to_date is not None:
            query = query.filter(record_date__lte=to_date)

        records = await query.order_by("-record_date", "-id").limit(limit)
        items = [self._to_activity_log(record) for record in records]
        return ActivityLogListResponse(
            summary=self._build_activity_summary(records),
            total=len(items),
            items=items,
        )

    async def get_activity_log(self, user: User, activity_log_id: int) -> ActivityLogResponse:
        record = await ActivityLog.get_or_none(id=activity_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생활습관 기록을 찾을 수 없습니다.")
        return self._to_activity_log(record)

    async def update_activity_log(
        self,
        user: User,
        activity_log_id: int,
        data: ActivityLogUpdateRequest,
    ) -> ActivityLogResponse:
        record = await ActivityLog.get_or_none(id=activity_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생활습관 기록을 찾을 수 없습니다.")
        self._ensure_today_record(record.record_date)

        update_data = data.model_dump(exclude_unset=True)
        alcohol_frequency = update_data.get("alcohol_frequency", record.alcohol_frequency)
        alcohol_amount = update_data.get("alcohol_amount", record.alcohol_amount)
        self._validate_activity_alcohol(alcohol_frequency, alcohol_amount)

        for field in ["alcohol_frequency", "alcohol_amount", "walking_days", "stress_level", "memo"]:
            if field in update_data:
                setattr(record, field, update_data[field])
        for field in ["sedentary_hours", "sleep_hours", "diet_score"]:
            if field in update_data:
                setattr(record, field, self._optional_decimal(update_data[field]))
        await record.save()
        return self._to_activity_log(record)

    async def delete_activity_log(self, user: User, activity_log_id: int) -> None:
        record = await ActivityLog.get_or_none(id=activity_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생활습관 기록을 찾을 수 없습니다.")
        self._ensure_today_record(record.record_date)
        await record.delete()

    async def get_health_goal(self, user: User) -> HealthGoalResponse:
        chronic_goal, lifestyle_goal = await self._get_or_create_health_goals(user)
        return HealthGoalResponse(
            chronic_disease_goal=self._to_chronic_disease_goal(chronic_goal),
            lifestyle_goal=self._to_lifestyle_goal(lifestyle_goal),
        )

    async def update_health_goal(self, user: User, data: HealthGoalUpdateRequest) -> HealthGoalResponse:
        chronic_goal, lifestyle_goal = await self._get_or_create_health_goals(user)

        if data.chronic_disease_goal is not None:
            for field, value in data.chronic_disease_goal.model_dump(exclude_unset=True).items():
                setattr(
                    chronic_goal,
                    field,
                    self._optional_decimal(value) if field in self._decimal_goal_fields() else value,
                )
            await chronic_goal.save()

        if data.lifestyle_goal is not None:
            for field, value in data.lifestyle_goal.model_dump(exclude_unset=True).items():
                setattr(
                    lifestyle_goal,
                    field,
                    self._optional_decimal(value) if field in self._decimal_goal_fields() else value,
                )
            await lifestyle_goal.save()

        return HealthGoalResponse(
            chronic_disease_goal=self._to_chronic_disease_goal(chronic_goal),
            lifestyle_goal=self._to_lifestyle_goal(lifestyle_goal),
        )

    async def create_exercise_log(self, user: User, data: ExerciseLogCreateRequest) -> OptionalRecordCreateResponse:
        record = await ExerciseLog.create(
            user=user,
            exercise_date=data.exercise_date,
            exercise_type=data.exercise_type.value,
            duration_minutes=data.duration_minutes,
            calories_burned=data.calories_burned,
            memo=data.memo,
        )
        return OptionalRecordCreateResponse(record_id=record.id, created_at=record.created_at)

    async def get_exercise_logs(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
        exercise_type: ExerciseType | None = None,
        limit: int = 100,
    ) -> ExerciseLogListResponse:
        query = ExerciseLog.filter(user_id=user.id)
        if from_date is not None:
            query = query.filter(exercise_date__gte=from_date)
        if to_date is not None:
            query = query.filter(exercise_date__lte=to_date)
        if exercise_type is not None:
            query = query.filter(exercise_type=exercise_type.value)

        records = await query.order_by("-exercise_date", "-id").limit(limit)
        items = [self._to_exercise_log(record) for record in records]
        return ExerciseLogListResponse(
            summary=self._build_exercise_summary(records),
            total=len(items),
            items=items,
        )

    async def get_exercise_log(self, user: User, exercise_log_id: int) -> ExerciseLogResponse:
        record = await ExerciseLog.get_or_none(id=exercise_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="운동 기록을 찾을 수 없습니다.")
        return self._to_exercise_log(record)

    async def update_exercise_log(
        self,
        user: User,
        exercise_log_id: int,
        data: ExerciseLogUpdateRequest,
    ) -> ExerciseLogResponse:
        record = await ExerciseLog.get_or_none(id=exercise_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="운동 기록을 찾을 수 없습니다.")
        self._ensure_today_record(record.exercise_date)

        update_data = data.model_dump(exclude_unset=True)
        exercise_date = update_data.get("exercise_date", record.exercise_date)
        if exercise_date != self._today():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="당일 운동 기록만 수정할 수 있습니다.")

        if "exercise_type" in update_data:
            record.exercise_type = update_data["exercise_type"].value
        for field in ["exercise_date", "duration_minutes", "calories_burned", "memo"]:
            if field in update_data:
                setattr(record, field, update_data[field])
        await record.save()
        return self._to_exercise_log(record)

    async def delete_exercise_log(self, user: User, exercise_log_id: int) -> None:
        record = await ExerciseLog.get_or_none(id=exercise_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="운동 기록을 찾을 수 없습니다.")
        self._ensure_today_record(record.exercise_date)
        await record.delete()

    async def create_meal_log(self, user: User, data: MealLogCreateRequest) -> MealLogCreateResponse:
        record = await MealLog.create(
            user=user,
            food_analysis_result_id=data.food_analysis_result_id,
            meal_date=data.meal_date,
            meal_type=data.meal_type.value,
            food_name=data.food_name,
            amount=data.amount,
            calories=data.calories,
            carbs_g=self._optional_decimal(data.carbs_g),
            protein_g=self._optional_decimal(data.protein_g),
            fat_g=self._optional_decimal(data.fat_g),
            sodium_mg=self._optional_decimal(data.sodium_mg),
            sugar_g=self._optional_decimal(data.sugar_g),
            fiber_g=self._optional_decimal(data.fiber_g),
            memo=data.memo,
        )
        return MealLogCreateResponse(meal_log_id=record.id, meal_date=record.meal_date, created_at=record.created_at)

    async def get_meal_logs(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
        meal_type: MealType | None = None,
        limit: int = 100,
    ) -> MealLogListResponse:
        query = MealLog.filter(user_id=user.id)
        if from_date is not None:
            query = query.filter(meal_date__gte=from_date)
        if to_date is not None:
            query = query.filter(meal_date__lte=to_date)
        if meal_type is not None:
            query = query.filter(meal_type=meal_type.value)

        records = await query.order_by("-meal_date", "-id").limit(limit)
        items = [self._to_meal_log(record) for record in records]
        return MealLogListResponse(
            daily_summary=self._build_meal_daily_summary(records),
            total=len(items),
            items=items,
        )

    async def get_meal_log(self, user: User, meal_log_id: int) -> MealLogResponse:
        record = await MealLog.get_or_none(id=meal_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="식단 기록을 찾을 수 없습니다.")
        return self._to_meal_log(record)

    async def update_meal_log(self, user: User, meal_log_id: int, data: MealLogUpdateRequest) -> MealLogResponse:
        record = await MealLog.get_or_none(id=meal_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="식단 기록을 찾을 수 없습니다.")

        update_data = data.model_dump(exclude_unset=True)
        if "meal_type" in update_data:
            record.meal_type = update_data.pop("meal_type").value
        for field, value in update_data.items():
            if field in self._meal_decimal_fields():
                setattr(record, field, self._optional_decimal(value))
            else:
                setattr(record, field, value)
        await record.save()
        return self._to_meal_log(record)

    async def delete_meal_log(self, user: User, meal_log_id: int) -> None:
        record = await MealLog.get_or_none(id=meal_log_id, user_id=user.id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="식단 기록을 찾을 수 없습니다.")
        await record.delete()

    async def get_health_statistics(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> HealthStatisticsResponse:
        period_end = to_date or self._today()
        period_start = from_date or (period_end - timedelta(days=6))
        if period_start > period_end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="조회 시작일은 종료일보다 늦을 수 없습니다."
            )

        vital_records = (
            await VitalRecord.filter(user_id=user.id, record_date__gte=period_start, record_date__lte=period_end)
            .order_by("-measured_at", "-id")
            .limit(200)
        )
        activity_logs = (
            await ActivityLog.filter(user_id=user.id, record_date__gte=period_start, record_date__lte=period_end)
            .order_by("-record_date", "-id")
            .limit(200)
        )
        exercise_logs = (
            await ExerciseLog.filter(user_id=user.id, exercise_date__gte=period_start, exercise_date__lte=period_end)
            .order_by("-exercise_date", "-id")
            .limit(200)
        )
        _, lifestyle_goal = await self._get_or_create_health_goals(user)

        activity_summary = self._build_activity_summary(activity_logs)
        exercise_summary = self._build_exercise_summary(exercise_logs)
        return HealthStatisticsResponse(
            period_start=period_start,
            period_end=period_end,
            vital_summary=self._build_vital_summary(vital_records),
            latest_vital_record=self._to_vital_record(vital_records[0]) if vital_records else None,
            activity_summary=activity_summary,
            latest_activity_log=self._to_activity_log(activity_logs[0]) if activity_logs else None,
            exercise_summary=exercise_summary,
            latest_exercise_log=self._to_exercise_log(exercise_logs[0]) if exercise_logs else None,
            goal_progress=self._build_goal_progress(
                lifestyle_goal=lifestyle_goal,
                activity_summary=activity_summary,
                exercise_summary=exercise_summary,
                period_days=(period_end - period_start).days + 1,
            ),
        )

    @staticmethod
    def _assess_dyslipidemia(user: User, lipid: LipidObesityRecord | None) -> MetricAssessmentItemResponse:
        if lipid is None:
            return MetricAssessmentItemResponse(
                status="UNAVAILABLE",
                reasons=["지질 수치가 입력되지 않았습니다."],
                missing_fields=DYSLIPIDEMIA_FIELDS,
            )

        values = {field: getattr(lipid, field) for field in DYSLIPIDEMIA_FIELDS}
        missing_fields = [field for field, value in values.items() if value is None]
        if all(value is None for value in values.values()):
            return MetricAssessmentItemResponse(
                status="UNAVAILABLE",
                reasons=["지질 수치가 입력되지 않았습니다."],
                missing_fields=missing_fields,
            )

        status_rank = 0
        reasons: list[str] = []
        for field, (caution, high, label) in DYSLIPIDEMIA_UPPER_RULES.items():
            rank, reason = HealthInputService._assess_upper_metric(values[field], caution, high, label)
            status_rank = max(status_rank, rank)
            if reason:
                reasons.append(reason)

        hdl = values["hdl_cholesterol"]
        hdl_threshold = 40 if user.gender == Gender.MALE else 50
        if hdl is not None and hdl < hdl_threshold:
            status_rank = max(status_rank, 2)
            reasons.append("HDL 콜레스테롤이 낮은 범위입니다.")

        if not reasons:
            reasons.append("입력된 지질 수치가 정상 범위입니다.")

        return MetricAssessmentItemResponse(
            status=HealthInputService._status_from_rank(status_rank),
            reasons=reasons,
            missing_fields=missing_fields,
        )

    @staticmethod
    def _assess_obesity(
        user: User,
        profile: UserProfile | None,
        health: ChronicHealthInput | None,
        lipid: LipidObesityRecord | None,
    ) -> MetricAssessmentItemResponse:
        bmi = HealthInputService._first_float(
            lipid.bmi if lipid else None,
            profile.bmi if profile else None,
            health.bmi if health else None,
        )
        waist = HealthInputService._first_float(
            lipid.waist_circumference if lipid else None,
            health.waist_circumference if health else None,
        )
        missing_fields = []
        if bmi is None:
            missing_fields.append("bmi")
        if waist is None:
            missing_fields.append("waist_circumference")
        if bmi is None and waist is None:
            return MetricAssessmentItemResponse(
                status="UNAVAILABLE",
                reasons=["BMI와 허리둘레가 입력되지 않았습니다."],
                missing_fields=missing_fields,
            )

        status_rank = 0
        reasons: list[str] = []
        if bmi is not None:
            if bmi >= 25:
                status_rank = max(status_rank, 2)
                reasons.append("BMI가 비만 범위입니다.")
            elif bmi >= 23:
                status_rank = max(status_rank, 1)
                reasons.append("BMI가 과체중 범위입니다.")

        waist_threshold = 90 if user.gender == Gender.MALE else 85
        if waist is not None:
            if waist >= waist_threshold:
                status_rank = max(status_rank, 2)
                reasons.append("허리둘레가 복부비만 기준 이상입니다.")

        if not reasons:
            reasons.append("BMI와 허리둘레가 정상 범위입니다.")

        return MetricAssessmentItemResponse(
            status=HealthInputService._status_from_rank(status_rank),
            reasons=reasons,
            missing_fields=missing_fields,
        )

    @staticmethod
    def _first_float(*values: Any) -> float | None:
        for value in values:
            if value is not None:
                return float(value)
        return None

    @staticmethod
    def _assess_upper_metric(value: int | None, caution: int, high: int, label: str) -> tuple[int, str | None]:
        if value is None:
            return 0, None
        if value >= high:
            return 2, f"{label}이 위험 범위입니다."
        if value >= caution:
            return 1, f"{label}이 주의 범위입니다."
        return 0, None

    @staticmethod
    def _status_from_rank(rank: int) -> str:
        return {0: "NORMAL", 1: "CAUTION", 2: "HIGH"}[rank]

    @staticmethod
    def _to_health_survey_record(snapshot: PredictionInputSnapshot) -> HealthSurveyRecordResponse:
        health = snapshot.chronic_health_input
        lifestyle = snapshot.lifestyle_input
        return HealthSurveyRecordResponse(
            health_input_id=snapshot.id,
            input_mode=snapshot.input_mode,
            age=health.age,
            gender=health.gender.value,
            height=float(health.height),
            weight=float(health.weight),
            bmi=float(health.bmi),
            waist_circumference=HealthInputService._optional_float(health.waist_circumference),
            sbp=health.sbp,
            dbp=health.dbp,
            glucose_fasting=health.glucose_fasting,
            diagnosed_diseases=health.diagnosed_diseases or [],
            medications=health.medications or [],
            last_checkup_period=health.last_checkup_period,
            fh_diabetes_father=health.fh_diabetes_father,
            fh_diabetes_mother=health.fh_diabetes_mother,
            fh_diabetes_sibling=health.fh_diabetes_sibling,
            fh_hypertension_father=health.fh_hypertension_father,
            fh_hypertension_mother=health.fh_hypertension_mother,
            fh_hypertension_sibling=health.fh_hypertension_sibling,
            family_history_ckd=health.family_history_ckd,
            smoking_status=lifestyle.smoking_status,
            alcohol_frequency=lifestyle.alcohol_frequency,
            alcohol_amount=lifestyle.alcohol_amount,
            walking_days=lifestyle.walking_days,
            sedentary_hours=HealthInputService._optional_float(lifestyle.sedentary_hours),
            exercise_frequency=lifestyle.exercise_frequency,
            physical_activity_min=lifestyle.physical_activity_min,
            sleep_hours=HealthInputService._optional_float(lifestyle.sleep_hours),
            stress_level=lifestyle.stress_level,
            diet_score=HealthInputService._optional_float(lifestyle.diet_score),
            created_at=snapshot.created_at,
        )

    @staticmethod
    def _to_lipid_obesity_record(record: LipidObesityRecord) -> LipidObesityRecordResponse:
        return LipidObesityRecordResponse(
            record_id=record.id,
            record_date=record.record_date,
            total_cholesterol=record.total_cholesterol,
            hdl_cholesterol=record.hdl_cholesterol,
            ldl_cholesterol=record.ldl_cholesterol,
            triglycerides=record.triglycerides,
            height=HealthInputService._optional_float(record.height_cm),
            weight=HealthInputService._optional_float(record.weight_kg),
            bmi=HealthInputService._optional_float(record.bmi),
            waist_circumference=HealthInputService._optional_float(record.waist_circumference),
            memo=record.memo,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_renal_record(record: RenalRecord) -> RenalRecordResponse:
        return RenalRecordResponse(
            record_id=record.id,
            record_date=record.record_date,
            creatinine=HealthInputService._optional_float(record.creatinine),
            egfr=HealthInputService._optional_float(record.egfr),
            bun=HealthInputService._optional_float(record.bun),
            urine_protein_pos=record.urine_protein_pos,
            memo=record.memo,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_vital_record(record: VitalRecord) -> VitalRecordResponse:
        return VitalRecordResponse(
            record_id=record.id,
            record_date=record.record_date,
            measured_at=record.measured_at,
            measure_type=VitalMeasureType(record.measure_type),
            sbp=record.sbp,
            dbp=record.dbp,
            glucose=record.glucose,
            memo=record.memo,
            is_critical=record.is_critical,
            status_label="CRITICAL" if record.is_critical else "NORMAL",
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_activity_log(record: ActivityLog) -> ActivityLogResponse:
        return ActivityLogResponse(
            activity_log_id=record.id,
            record_date=record.record_date,
            alcohol_frequency=record.alcohol_frequency,
            alcohol_amount=record.alcohol_amount,
            walking_days=record.walking_days,
            sedentary_hours=HealthInputService._optional_float(record.sedentary_hours),
            sleep_hours=HealthInputService._optional_float(record.sleep_hours),
            stress_level=record.stress_level,
            diet_score=HealthInputService._optional_float(record.diet_score),
            memo=record.memo,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    async def _get_or_create_health_goals(user: User) -> tuple[UserChronicDiseaseGoal, UserLifestyleGoal]:
        chronic_goal, _ = await UserChronicDiseaseGoal.get_or_create(user_id=user.id)
        lifestyle_goal, _ = await UserLifestyleGoal.get_or_create(user_id=user.id, defaults=DEFAULT_LIFESTYLE_GOAL)
        return chronic_goal, lifestyle_goal

    @staticmethod
    def _to_chronic_disease_goal(goal: UserChronicDiseaseGoal) -> ChronicDiseaseGoalResponse:
        return ChronicDiseaseGoalResponse(
            target_systolic_bp=goal.target_systolic_bp,
            target_diastolic_bp=goal.target_diastolic_bp,
            target_fasting_glucose=goal.target_fasting_glucose,
            target_postprandial_glucose=goal.target_postprandial_glucose,
            target_hba1c=HealthInputService._optional_float(goal.target_hba1c),
            target_ldl_cholesterol=goal.target_ldl_cholesterol,
            target_hdl_cholesterol=goal.target_hdl_cholesterol,
            target_triglycerides=goal.target_triglycerides,
            target_bmi=HealthInputService._optional_float(goal.target_bmi),
            target_weight_kg=HealthInputService._optional_float(goal.target_weight_kg),
            target_egfr=HealthInputService._optional_float(goal.target_egfr),
            updated_at=goal.updated_at,
        )

    @staticmethod
    def _to_lifestyle_goal(goal: UserLifestyleGoal) -> LifestyleGoalResponse:
        return LifestyleGoalResponse(
            target_steps=goal.target_steps,
            target_water_ml=goal.target_water_ml,
            target_exercise_minutes=goal.target_exercise_minutes,
            target_sleep_hours=HealthInputService._optional_float(goal.target_sleep_hours),
            target_diet_score=HealthInputService._optional_float(goal.target_diet_score),
            updated_at=goal.updated_at,
        )

    @staticmethod
    def _to_exercise_log(record: ExerciseLog) -> ExerciseLogResponse:
        return ExerciseLogResponse(
            exercise_log_id=record.id,
            exercise_date=record.exercise_date,
            exercise_type=ExerciseType(record.exercise_type),
            duration_minutes=record.duration_minutes,
            calories_burned=record.calories_burned,
            memo=record.memo,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_meal_log(record: MealLog) -> MealLogResponse:
        return MealLogResponse(
            meal_log_id=record.id,
            food_analysis_result_id=record.food_analysis_result_id,
            meal_date=record.meal_date,
            meal_type=MealType(record.meal_type),
            food_name=record.food_name,
            amount=record.amount,
            calories=record.calories,
            carbs_g=HealthInputService._optional_float(record.carbs_g),
            protein_g=HealthInputService._optional_float(record.protein_g),
            fat_g=HealthInputService._optional_float(record.fat_g),
            sodium_mg=HealthInputService._optional_float(record.sodium_mg),
            sugar_g=HealthInputService._optional_float(record.sugar_g),
            fiber_g=HealthInputService._optional_float(record.fiber_g),
            memo=record.memo,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _build_vital_summary(records: list[VitalRecord]) -> VitalRecordSummaryResponse:
        sbp_values = [record.sbp for record in records if record.sbp is not None]
        dbp_values = [record.dbp for record in records if record.dbp is not None]
        glucose_values = [record.glucose for record in records if record.glucose is not None]
        return VitalRecordSummaryResponse(
            avg_sbp=HealthInputService._average(sbp_values),
            avg_dbp=HealthInputService._average(dbp_values),
            avg_glucose=HealthInputService._average(glucose_values),
            critical_count=sum(1 for record in records if record.is_critical),
        )

    @staticmethod
    def _build_activity_summary(records: list[ActivityLog]) -> ActivityLogSummaryResponse:
        walking_days = [record.walking_days for record in records if record.walking_days is not None]
        sedentary_hours = [float(record.sedentary_hours) for record in records if record.sedentary_hours is not None]
        sleep_hours = [float(record.sleep_hours) for record in records if record.sleep_hours is not None]
        stress_levels = [record.stress_level for record in records if record.stress_level is not None]
        diet_scores = [float(record.diet_score) for record in records if record.diet_score is not None]
        return ActivityLogSummaryResponse(
            avg_walking_days=HealthInputService._average_float(walking_days),
            avg_sedentary_hours=HealthInputService._average_float(sedentary_hours),
            avg_sleep_hours=HealthInputService._average_float(sleep_hours),
            avg_stress_level=HealthInputService._average_float(stress_levels),
            avg_diet_score=HealthInputService._average_float(diet_scores),
            logged_days=len(records),
        )

    @staticmethod
    def _build_exercise_summary(records: list[ExerciseLog]) -> ExerciseLogSummaryResponse:
        return ExerciseLogSummaryResponse(
            total_duration_minutes=sum(record.duration_minutes for record in records),
            total_calories_burned=sum(record.calories_burned or 0 for record in records),
            logged_count=len(records),
        )

    @staticmethod
    def _build_meal_daily_summary(records: list[MealLog]) -> list[MealDailySummaryResponse]:
        grouped: dict[date, list[MealLog]] = {}
        for record in records:
            grouped.setdefault(record.meal_date, []).append(record)

        return [
            MealDailySummaryResponse(
                meal_date=meal_date,
                meal_count=len(day_records),
                total_calories=sum(record.calories or 0 for record in day_records),
                total_sodium_mg=round(
                    sum(float(record.sodium_mg or 0) for record in day_records),
                    2,
                ),
                total_sugar_g=round(
                    sum(float(record.sugar_g or 0) for record in day_records),
                    2,
                ),
                total_fiber_g=round(
                    sum(float(record.fiber_g or 0) for record in day_records),
                    2,
                ),
            )
            for meal_date, day_records in sorted(grouped.items(), reverse=True)
        ]

    @staticmethod
    def _build_goal_progress(
        lifestyle_goal: UserLifestyleGoal,
        activity_summary: ActivityLogSummaryResponse,
        exercise_summary: ExerciseLogSummaryResponse,
        period_days: int,
    ) -> list[HealthGoalProgressResponse]:
        return [
            HealthInputService._build_progress_item(
                metric="EXERCISE_MINUTES",
                current_value=float(exercise_summary.total_duration_minutes),
                target_value=float(lifestyle_goal.target_exercise_minutes * period_days),
                unit="minutes",
            ),
            HealthInputService._build_progress_item(
                metric="SLEEP_HOURS",
                current_value=activity_summary.avg_sleep_hours,
                target_value=HealthInputService._optional_float(lifestyle_goal.target_sleep_hours),
                unit="hours",
            ),
            HealthInputService._build_progress_item(
                metric="DIET_SCORE",
                current_value=activity_summary.avg_diet_score,
                target_value=HealthInputService._optional_float(lifestyle_goal.target_diet_score),
                unit="score",
            ),
        ]

    @staticmethod
    def _build_progress_item(
        metric: str,
        current_value: float | None,
        target_value: float | None,
        unit: str,
    ) -> HealthGoalProgressResponse:
        progress_rate = HealthInputService._progress_rate(current_value, target_value)
        return HealthGoalProgressResponse(
            metric=metric,
            current_value=current_value,
            target_value=target_value,
            unit=unit,
            progress_rate=progress_rate,
            status=HealthInputService._progress_status(progress_rate),
        )

    @staticmethod
    def _progress_rate(current_value: float | None, target_value: float | None) -> float | None:
        if current_value is None or target_value is None or target_value <= 0:
            return None
        return round(min(current_value / target_value, 1.0) * 100, 1)

    @staticmethod
    def _progress_status(progress_rate: float | None) -> str:
        if progress_rate is None:
            return "UNAVAILABLE"
        if progress_rate >= 100:
            return "ACHIEVED"
        return "IN_PROGRESS"

    @staticmethod
    def _average(values: list[int]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    @staticmethod
    def _average_float(values: list[int | float]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    @staticmethod
    def _decimal_goal_fields() -> set[str]:
        return {
            "target_hba1c",
            "target_bmi",
            "target_weight_kg",
            "target_egfr",
            "target_sleep_hours",
            "target_diet_score",
        }

    @staticmethod
    def _meal_decimal_fields() -> set[str]:
        return {"carbs_g", "protein_g", "fat_g", "sodium_mg", "sugar_g", "fiber_g"}

    @staticmethod
    def _validate_activity_alcohol(alcohol_frequency: int | None, alcohol_amount: int | None) -> None:
        if alcohol_frequency == 0 and alcohol_amount is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="음주 빈도가 없음이면 음주량을 입력할 수 없습니다.",
            )
        if alcohol_frequency in {1, 3} and alcohol_amount is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="음주 빈도가 있으면 음주량이 필요합니다.",
            )

    @staticmethod
    def _validate_vital_values(measure_type: str, sbp: int | None, dbp: int | None, glucose: int | None) -> None:
        if measure_type.startswith("BP_"):
            if sbp is None or dbp is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="혈압 기록에는 수축기·이완기 혈압이 필요합니다.",
                )
            if glucose is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="혈압 기록에는 혈당을 입력할 수 없습니다."
                )
        if measure_type.startswith("GLUCOSE_"):
            if glucose is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="혈당 기록에는 혈당 수치가 필요합니다."
                )
            if sbp is not None or dbp is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="혈당 기록에는 혈압을 입력할 수 없습니다."
                )

    @staticmethod
    def _is_vital_critical(measure_type: str, sbp: int | None, dbp: int | None, glucose: int | None) -> bool:
        if measure_type.startswith("BP_"):
            return (sbp is not None and sbp >= 180) or (dbp is not None and dbp >= 110)
        if measure_type.startswith("GLUCOSE_"):
            return glucose is not None and glucose >= 200
        return False

    @staticmethod
    def _ensure_today_record(record_date: date) -> None:
        if record_date != HealthInputService._today():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="당일 기록만 수정 또는 삭제할 수 있습니다."
            )

    @staticmethod
    def _today() -> date:
        return datetime.now(config.TIMEZONE).date()

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        return float(value) if value is not None else None

    @staticmethod
    def _optional_decimal(value: int | float | None) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None


class PredictionService:
    async def create_task(self, user: User, data: PredictionTaskCreateRequest) -> PredictionTaskCreateResponse:
        survey_snapshot = await PredictionInputSnapshot.get_or_none(id=data.health_input_id, user_id=user.id)
        if survey_snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="건강 설문 입력을 찾을 수 없습니다.")

        lipid = await LipidObesityRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        renal = await RenalRecord.filter(user_id=user.id).order_by("-record_date", "-created_at").first()
        survey_health = await ChronicHealthInput.get(id=survey_snapshot.chronic_health_input_id)
        missing_fields = self._missing_optional_measurements(survey_health, lipid, renal)

        snapshot = await PredictionInputSnapshot.create(
            user=user,
            input_mode=survey_snapshot.input_mode,
            chronic_health_input_id=survey_snapshot.chronic_health_input_id,
            lifestyle_input_id=survey_snapshot.lifestyle_input_id,
            lipid_obesity_record=lipid,
            renal_record=renal,
            used_default_values=bool(missing_fields),
            missing_fields=missing_fields,
        )
        task = await PredictionTask.create(
            user=user,
            task_uuid=str(uuid.uuid4()),
            input_snapshot=snapshot,
            prediction_mode=PredictionMode(data.prediction_mode),
            progress_percent=PREDICTION_PROGRESS[PredictionStatus.PENDING][0],
            current_step=PREDICTION_PROGRESS[PredictionStatus.PENDING][1],
        )
        return PredictionTaskCreateResponse(
            task_uuid=task.task_uuid,
            status=PredictionStatus.PENDING.value,
            prediction_mode=task.prediction_mode.value,
        )

    async def process_task(self, task_uuid: str, user_id: int) -> None:
        task = await PredictionTask.get_or_none(task_uuid=task_uuid, user_id=user_id)
        if task is None:
            return
        started = time.perf_counter()
        task.status = PredictionStatus.RUNNING
        task.progress_percent = PREDICTION_PROGRESS[PredictionStatus.RUNNING][0]
        task.current_step = PREDICTION_PROGRESS[PredictionStatus.RUNNING][1]
        task.started_at = datetime.now(config.TIMEZONE)
        await task.save(update_fields=["status", "progress_percent", "current_step", "started_at"])

        try:
            raw_input, snapshot = await self._build_model_input(task.input_snapshot_id)
            disease_predictions = await asyncio.to_thread(self._run_models, raw_input)
            completeness = self._input_completeness(snapshot.missing_fields)
            at_risk = [disease for disease, values in disease_predictions.items() if values["is_at_risk"]]
            result = await PredictionResult.create(
                task=task,
                user_id=user_id,
                overall_risk_level="HIGH" if at_risk else "LOW",
                lifestyle_priority=at_risk,
                input_completeness=completeness,
                inference_ms=int((time.perf_counter() - started) * 1000),
                disclaimer=DISCLAIMER,
            )
            health = await ChronicHealthInput.get(id=snapshot.chronic_health_input_id)
            lifestyle = await LifestyleInput.get(id=snapshot.lifestyle_input_id)
            lipid = (
                await LipidObesityRecord.get(id=snapshot.lipid_obesity_record_id)
                if snapshot.lipid_obesity_record_id is not None
                else None
            )
            renal = await RenalRecord.get(id=snapshot.renal_record_id) if snapshot.renal_record_id is not None else None
            for disease, values in disease_predictions.items():
                values["risk_factors"] = self._risk_factors(disease, health, lifestyle, lipid, renal)
                await PredictionResultItem.create(result=result, disease_code=disease, **values)
            task.status = PredictionStatus.SUCCESS
        except Exception as exc:
            task.status = PredictionStatus.FAILED
            task.error_message = str(exc)[:500]
        task.progress_percent = self._task_progress(task.status)[0]
        task.current_step = self._task_progress(task.status)[1]
        task.completed_at = datetime.now(config.TIMEZONE)
        await task.save(update_fields=["status", "progress_percent", "current_step", "error_message", "completed_at"])

    async def get_task_status(self, user: User, task_uuid: str) -> PredictionTaskStatusResponse:
        task = await PredictionTask.get_or_none(task_uuid=task_uuid, user_id=user.id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예측 작업을 찾을 수 없습니다.")
        result = await PredictionResult.get_or_none(task_id=task.id)
        progress_percent, current_step = (
            (task.progress_percent, task.current_step) if task.current_step else self._task_progress(task.status)
        )
        return PredictionTaskStatusResponse(
            task_uuid=task.task_uuid,
            status=task.status.value,
            progress_percent=progress_percent,
            current_step=current_step,
            result_id=result.id if result else None,
            error_message=task.error_message,
        )

    async def get_result(self, user: User, result_id: int) -> PredictionResultResponse:
        result = await PredictionResult.get_or_none(id=result_id, user_id=user.id).prefetch_related("items", "task")
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예측 결과를 찾을 수 없습니다.")
        disease_risks = {}
        response_codes = {"DIABETES": "diabetes", "HYPERTENSION": "hypertension", "CKD": "kidney"}
        for item in result.items:
            disease_risks[response_codes[item.disease_code]] = {
                "probability": float(item.probability),
                "threshold": float(item.threshold),
                "is_at_risk": item.is_at_risk,
                "risk_level": item.risk_level,
                "message": item.message,
                "risk_factors": item.risk_factors or [],
            }
        return PredictionResultResponse(
            result_id=result.id,
            prediction_mode=result.task.prediction_mode.value,
            disease_risks=disease_risks,
            input_completeness=InputCompletenessResponse(**result.input_completeness),
            disclaimer=result.disclaimer,
        )

    async def create_feedback(
        self,
        user: User,
        result_id: int,
        data: PredictionFeedbackCreateRequest,
    ) -> PredictionFeedbackCreateResponse:
        result = await PredictionResult.get_or_none(id=result_id, user_id=user.id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예측 결과를 찾을 수 없습니다.")

        exists = await PredictionFeedback.exists(prediction_result_id=result.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 피드백을 등록한 예측 결과입니다.")

        feedback = await PredictionFeedback.create(
            prediction_result=result,
            user=user,
            feedback_type=data.feedback_type.value,
            actual_diagnosis=data.actual_diagnosis,
            comment=data.comment,
        )
        return PredictionFeedbackCreateResponse(
            feedback_id=feedback.id,
            prediction_result_id=result.id,
            feedback_type=data.feedback_type,
            created_at=feedback.created_at,
        )

    @staticmethod
    def _task_progress(task_status: PredictionStatus) -> tuple[int, str]:
        return PREDICTION_PROGRESS[task_status]

    @staticmethod
    def _risk_factors(
        disease_code: str,
        health: ChronicHealthInput,
        lifestyle: LifestyleInput,
        lipid: LipidObesityRecord | None,
        renal: RenalRecord | None,
    ) -> list[str]:
        if disease_code == "DIABETES":
            return PredictionService._diabetes_risk_factors(health, lifestyle, lipid)
        if disease_code == "HYPERTENSION":
            return PredictionService._hypertension_risk_factors(health, lipid)
        if disease_code == "CKD":
            return PredictionService._ckd_risk_factors(health, renal)
        return []

    @staticmethod
    def _diabetes_risk_factors(
        health: ChronicHealthInput,
        lifestyle: LifestyleInput,
        lipid: LipidObesityRecord | None,
    ) -> list[str]:
        factors: list[str] = []
        if health.glucose_fasting is not None and health.glucose_fasting >= 126:
            factors.append("공복혈당이 당뇨 의심 기준 이상입니다.")
        if float(health.bmi) >= 25:
            factors.append("BMI가 비만 범위입니다.")
        if health.fh_diabetes_father or health.fh_diabetes_mother or health.fh_diabetes_sibling:
            factors.append("당뇨 가족력이 입력되었습니다.")
        if lifestyle.walking_days is not None and lifestyle.walking_days < 3:
            factors.append("주간 걷기 일수가 낮은 편입니다.")
        factors.extend(PredictionService._abdominal_obesity_factors(health, lipid))
        return factors

    @staticmethod
    def _hypertension_risk_factors(health: ChronicHealthInput, lipid: LipidObesityRecord | None) -> list[str]:
        factors: list[str] = []
        if health.sbp is not None and health.sbp >= 140:
            factors.append("수축기 혈압이 높은 범위입니다.")
        if health.dbp is not None and health.dbp >= 90:
            factors.append("이완기 혈압이 높은 범위입니다.")
        if float(health.bmi) >= 25:
            factors.append("BMI가 비만 범위입니다.")
        if health.fh_hypertension_father or health.fh_hypertension_mother or health.fh_hypertension_sibling:
            factors.append("고혈압 가족력이 입력되었습니다.")
        factors.extend(PredictionService._abdominal_obesity_factors(health, lipid))
        return factors

    @staticmethod
    def _ckd_risk_factors(health: ChronicHealthInput, renal: RenalRecord | None) -> list[str]:
        factors: list[str] = []
        diagnoses = set(health.diagnosed_diseases)
        if renal and renal.creatinine is not None and float(renal.creatinine) >= 1.3:
            factors.append("크레아티닌 수치가 높은 범위입니다.")
        if renal and renal.bun is not None and float(renal.bun) >= 20:
            factors.append("BUN 수치가 높은 범위입니다.")
        if renal and renal.urine_protein_pos:
            factors.append("소변 단백 양성으로 입력되었습니다.")
        if "DIABETES" in diagnoses or "HYPERTENSION" in diagnoses:
            factors.append("당뇨 또는 고혈압 진단 이력이 입력되었습니다.")
        return factors

    @staticmethod
    def _abdominal_obesity_factors(health: ChronicHealthInput, lipid: LipidObesityRecord | None) -> list[str]:
        waist = HealthInputService._first_float(
            lipid.waist_circumference if lipid else None,
            health.waist_circumference,
        )
        waist_threshold = 90 if health.gender == Gender.MALE else 85
        if waist is not None and waist >= waist_threshold:
            return ["허리둘레가 복부비만 기준 이상입니다."]
        return []

    @staticmethod
    def _missing_optional_measurements(
        health: ChronicHealthInput,
        lipid: LipidObesityRecord | None,
        renal: RenalRecord | None,
    ) -> list[str]:
        fields: list[str] = []
        lipid_fields = ["total_cholesterol", "hdl_cholesterol", "ldl_cholesterol", "triglycerides"]
        renal_fields = ["creatinine", "bun", "urine_protein_pos"]
        for field in lipid_fields:
            if lipid is None or getattr(lipid, field) is None:
                fields.append(field)
        if (lipid is None or lipid.waist_circumference is None) and health.waist_circumference is None:
            fields.append("waist_circumference")
        for field in renal_fields:
            if renal is None or getattr(renal, field) is None:
                fields.append(field)
        return fields

    @staticmethod
    def _input_completeness(missing_fields: list[str]) -> dict[str, Any]:
        if not missing_fields:
            return {"used_default_values": False, "missing_fields": [], "message": "입력된 검사 수치를 반영했습니다."}
        return {
            "used_default_values": True,
            "missing_fields": missing_fields,
            "message": "일부 검사 수치가 입력되지 않아 일반 기준값을 사용했습니다. 수치를 추가하면 더 개인화된 결과를 확인할 수 있습니다.",
        }

    async def _build_model_input(self, snapshot_id: int) -> tuple[dict[str, Any], PredictionInputSnapshot]:
        snapshot = await PredictionInputSnapshot.get(id=snapshot_id)
        health = await ChronicHealthInput.get(id=snapshot.chronic_health_input_id)
        lifestyle = await LifestyleInput.get(id=snapshot.lifestyle_input_id)
        lipid = (
            await LipidObesityRecord.get(id=snapshot.lipid_obesity_record_id)
            if snapshot.lipid_obesity_record_id is not None
            else None
        )
        renal = await RenalRecord.get(id=snapshot.renal_record_id) if snapshot.renal_record_id is not None else None
        diagnoses = set(health.diagnosed_diseases)
        medications = set(health.medications)
        raw: dict[str, Any] = {
            "age": health.age,
            "sex": 1 if health.gender == Gender.MALE else 2,
            "height": float(health.height),
            "weight": float(health.weight),
            "bmi": float(health.bmi),
            "sbp": health.sbp,
            "dbp": health.dbp,
            "glucose_fasting": health.glucose_fasting,
            "waist_circumference": (
                float(health.waist_circumference) if health.waist_circumference is not None else None
            ),
            "dx_diabetes": int("DIABETES" in diagnoses),
            "dx_hypertension": int("HYPERTENSION" in diagnoses),
            "dx_dyslipidemia": int("DYSLIPIDEMIA" in diagnoses),
            "tx_diabetes": int("DIABETES" in medications),
            "tx_hypertension": int("HYPERTENSION" in medications),
            "fh_diabetes_father": int(health.fh_diabetes_father),
            "fh_diabetes_mother": int(health.fh_diabetes_mother),
            "fh_diabetes_sibling": int(health.fh_diabetes_sibling),
            "fh_hypertension_father": int(health.fh_hypertension_father),
            "fh_hypertension_mother": int(health.fh_hypertension_mother),
            "fh_hypertension_sibling": int(health.fh_hypertension_sibling),
            "fh_diabetes_parent": int(health.fh_diabetes_father or health.fh_diabetes_mother),
            "fh_hypertension_parent": int(health.fh_hypertension_father or health.fh_hypertension_mother),
            **self._to_model_lifestyle_input(lifestyle),
        }
        if lipid:
            raw.update(
                {
                    "total_cholesterol": lipid.total_cholesterol,
                    "hdl_cholesterol": lipid.hdl_cholesterol,
                    "ldl_cholesterol": lipid.ldl_cholesterol,
                    "triglycerides": lipid.triglycerides,
                }
            )
            if lipid.waist_circumference is not None:
                raw["waist_circumference"] = float(lipid.waist_circumference)
        if renal:
            raw.update(
                {
                    "creatinine": float(renal.creatinine) if renal.creatinine is not None else None,
                    "bun": float(renal.bun) if renal.bun is not None else None,
                    "urine_protein": int(renal.urine_protein_pos) if renal.urine_protein_pos is not None else None,
                }
            )
        return {key: value for key, value in raw.items() if value is not None}, snapshot

    @staticmethod
    def _to_model_lifestyle_input(lifestyle: LifestyleInput) -> dict[str, Any]:
        smoking_map = {0: 8, 1: 3, 2: 1}
        alcohol_frequency_map = {0: 1, 1: 3, 3: 4}
        return {
            "smoking_status": smoking_map[lifestyle.smoking_status],
            "alcohol_frequency": alcohol_frequency_map[lifestyle.alcohol_frequency],
            "alcohol_amount": lifestyle.alcohol_amount,
            "walking_days": lifestyle.walking_days,
            "sedentary_hours": float(lifestyle.sedentary_hours) if lifestyle.sedentary_hours is not None else None,
        }

    @staticmethod
    def _run_models(raw_input: dict[str, Any]) -> dict[str, dict[str, Any]]:
        import pandas as pd

        from ai_worker.tasks.inference_preprocess import predict

        model_input = pd.DataFrame([raw_input])
        results: dict[str, dict[str, Any]] = {}
        for model_disease, (disease_code, display_name) in DISEASE_MAPPINGS.items():
            output = predict(model_input, model_disease, MODELS_DIR, mode="screening").iloc[0]
            at_risk = bool(output["is_at_risk"])
            results[disease_code] = {
                "probability": Decimal(str(round(float(output["probability"]), 6))),
                "threshold": Decimal(str(round(float(output["threshold"]), 5))),
                "is_at_risk": at_risk,
                "risk_level": "HIGH" if at_risk else "LOW",
                "message": (
                    f"{display_name} 위험 신호가 감지되었습니다. 전문의와 상담해 보세요."
                    if at_risk
                    else f"{display_name} 위험 신호는 현재 기준에서 높지 않습니다."
                ),
            }
        return results
