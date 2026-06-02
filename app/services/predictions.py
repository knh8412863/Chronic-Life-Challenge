import asyncio
import time
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.core import config
from app.dtos.predictions import (
    HealthSurveyCreateRequest,
    HealthSurveyCreateResponse,
    InputCompletenessResponse,
    LipidObesityRecordCreateRequest,
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
)
from app.models.predictions import (
    ChronicHealthInput,
    LifestyleInput,
    LipidObesityRecord,
    PredictionFeedback,
    PredictionInputSnapshot,
    PredictionMode,
    PredictionResult,
    PredictionResultItem,
    PredictionStatus,
    PredictionTask,
    RenalRecord,
    UserProfile,
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
