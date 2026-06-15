from datetime import date
from typing import Any

from fastapi import HTTPException, status

from app.core import config
from app.dtos.advices import (
    AdviceFeedbackCreateRequest,
    AdviceFeedbackCreateResponse,
    AdviceFeedbackType,
    AdviceGenerateRequest,
    AdviceHistoryItemResponse,
    AdviceTriggerType,
    DailyAdviceResponse,
)
from app.models.advices import AdviceFeedback, LLMAdvice
from app.models.predictions import ActivityLog, ChronicHealthInput, ExerciseLog, MealLog, PredictionResult, VitalRecord
from app.models.users import User
from app.services.llm_advice import OPENAI_PROVIDER, AdviceLLMError, AdviceLLMResult, OpenAIAdviceClient
from app.services.notifications import NotificationService
from app.services.predictions import HealthInputService

RULE_BASED_PROVIDER = "RULE_BASED"
RULE_BASED_MODEL = "daily-advice-rules-v1"
ADVICE_TITLE = "오늘의 건강 조언"
MAX_ADVICE_LENGTH = 200
ADVICE_DISCLAIMER = "본 조언은 진단이 아니며, 증상이나 우려가 있으면 전문의와 상담하세요."
MAX_DAILY_MANUAL_REGENERATIONS = 2


class AdviceService:
    async def get_today(self, user: User) -> DailyAdviceResponse:
        today = HealthInputService._today()
        advice = await self._latest_advice(user.id, today)
        if advice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="오늘 생성된 조언이 없습니다.")
        latest_record_at = await self._latest_today_record_at(user.id, today)
        if latest_record_at is not None and advice.created_at < latest_record_at:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="오늘 건강 기록이 갱신되었습니다. 조언을 새로 받아보세요.",
            )
        remaining = await self._remaining_manual_regeneration_count(user.id, today)
        return self._to_response(advice, generated=False, remaining_regeneration_count=remaining)

    async def generate_today(self, user: User, data: AdviceGenerateRequest) -> DailyAdviceResponse:
        today = HealthInputService._today()
        if data.trigger_type == AdviceTriggerType.AUTO:
            existing = await LLMAdvice.filter(
                user_id=user.id,
                advice_date=today,
                trigger_type=data.trigger_type.value,
            ).first()
            if existing:
                remaining = await self._remaining_manual_regeneration_count(user.id, today)
                return self._to_response(existing, generated=False, remaining_regeneration_count=remaining)
        else:
            remaining = await self._remaining_manual_regeneration_count(user.id, today)
            if remaining <= 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="오늘 조언 재생성 가능 횟수를 모두 사용했습니다.",
                )

        context = await self._build_context(user)
        if data.trigger_type == AdviceTriggerType.MANUAL:
            context["manual_generation_no"] = MAX_DAILY_MANUAL_REGENERATIONS - remaining + 1
        llm_result = await self._generate_llm_advice(context)
        advice_text = llm_result.advice_text if llm_result else self._build_rule_based_advice(context)
        advice = await LLMAdvice.create(
            user=user,
            advice_date=today,
            context_snapshot=context,
            prompt_summary=self._prompt_summary(context),
            advice_text=advice_text,
            provider=llm_result.provider if llm_result else RULE_BASED_PROVIDER,
            model_name=llm_result.model_name if llm_result else RULE_BASED_MODEL,
            input_tokens=llm_result.input_tokens if llm_result else 0,
            output_tokens=llm_result.output_tokens if llm_result else 0,
            cache_read_tokens=llm_result.cache_read_tokens if llm_result else 0,
            trigger_type=data.trigger_type.value,
        )
        await NotificationService().notify_advice_created(user_id=user.id, advice_id=advice.id)
        remaining = await self._remaining_manual_regeneration_count(user.id, today)
        return self._to_response(advice, generated=True, remaining_regeneration_count=remaining)

    async def get_history(
        self,
        user: User,
        sort: str = "LATEST",
        limit: int = 20,
    ) -> list[AdviceHistoryItemResponse]:
        order_by = "-created_at" if sort == "LATEST" else "created_at"
        advices = await LLMAdvice.filter(user_id=user.id).order_by(order_by).limit(limit)
        advice_ids = [advice.id for advice in advices]
        feedbacks = await AdviceFeedback.filter(advice_id__in=advice_ids) if advice_ids else []
        feedback_by_advice_id = {feedback.advice_id: feedback for feedback in feedbacks}
        return [self._to_history_item(advice, feedback_by_advice_id.get(advice.id)) for advice in advices]

    async def create_feedback(
        self,
        user: User,
        advice_id: int,
        data: AdviceFeedbackCreateRequest,
    ) -> AdviceFeedbackCreateResponse:
        advice = await LLMAdvice.get_or_none(id=advice_id, user_id=user.id)
        if advice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="오늘의 조언을 찾을 수 없습니다.")

        exists = await AdviceFeedback.exists(advice_id=advice.id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 피드백을 등록한 조언입니다.")

        feedback = await AdviceFeedback.create(
            advice=advice,
            user=user,
            feedback_type=data.feedback_type.value,
            comment=data.comment,
        )
        return self._to_feedback_response(feedback, advice.id)

    @staticmethod
    async def _latest_advice(user_id: int, advice_date: date) -> LLMAdvice | None:
        return await LLMAdvice.filter(user_id=user_id, advice_date=advice_date).order_by("-created_at").first()

    @staticmethod
    async def _remaining_manual_regeneration_count(user_id: int, advice_date: date) -> int:
        manual_count = await LLMAdvice.filter(
            user_id=user_id,
            advice_date=advice_date,
            trigger_type=AdviceTriggerType.MANUAL.value,
        ).count()
        return max(MAX_DAILY_MANUAL_REGENERATIONS - manual_count, 0)

    @staticmethod
    async def _build_context(user: User) -> dict[str, Any]:
        latest_health = await ChronicHealthInput.filter(user_id=user.id).order_by("-created_at").first()
        latest_prediction = (
            await PredictionResult.filter(user_id=user.id).order_by("-created_at").prefetch_related("items").first()
        )
        metric_assessment = await HealthInputService().get_metric_assessments(user)
        today = HealthInputService._today()
        today_vitals = await VitalRecord.filter(user_id=user.id, record_date=today).order_by("-measured_at", "-id")
        today_activity = await ActivityLog.filter(user_id=user.id, record_date=today).order_by("-created_at", "-id")
        today_exercises = await ExerciseLog.filter(user_id=user.id, exercise_date=today).order_by("-created_at", "-id")
        today_meals = await MealLog.filter(user_id=user.id, meal_date=today).order_by("-created_at", "-id")

        at_risk_diseases = []
        disease_risks = {}
        if latest_prediction:
            for item in latest_prediction.items:
                disease_risks[item.disease_code] = {
                    "risk_level": item.risk_level,
                    "is_at_risk": item.is_at_risk,
                    "risk_factors": item.risk_factors or [],
                }
                if item.is_at_risk:
                    at_risk_diseases.append(item.disease_code)

        return {
            "age": latest_health.age if latest_health else None,
            "diagnosed_diseases": latest_health.diagnosed_diseases if latest_health else [],
            "at_risk_diseases": at_risk_diseases,
            "disease_risks": disease_risks,
            "metric_assessment": {
                "dyslipidemia": metric_assessment.dyslipidemia.model_dump(),
                "obesity": metric_assessment.obesity.model_dump(),
            },
            "today_records": {
                "vitals": [
                    {
                        "measure_type": item.measure_type,
                        "sbp": item.sbp,
                        "dbp": item.dbp,
                        "glucose": item.glucose,
                    }
                    for item in today_vitals
                ],
                "activity": [
                    {
                        "steps": item.steps,
                        "exercise_minutes": item.exercise_minutes,
                        "water_ml": item.water_ml,
                        "sleep_hours": float(item.sleep_hours) if item.sleep_hours is not None else None,
                        "stress_level": item.stress_level,
                    }
                    for item in today_activity
                ],
                "exercise_minutes": sum(item.duration_minutes for item in today_exercises),
                "meals": [
                    {
                        "meal_type": item.meal_type,
                        "food_name": item.food_name,
                        "calories": item.calories,
                        "sodium_mg": float(item.sodium_mg) if item.sodium_mg is not None else None,
                        "sugar_g": float(item.sugar_g) if item.sugar_g is not None else None,
                    }
                    for item in today_meals
                ],
            },
            "generated_at_timezone": str(config.TIMEZONE),
        }

    @staticmethod
    def _build_rule_based_advice(context: dict[str, Any]) -> str:
        parts: list[str] = []
        at_risk = context.get("at_risk_diseases", [])
        metric = context.get("metric_assessment", {})

        if at_risk:
            disease_names = AdviceService._disease_names(at_risk)
            parts.append(f"{', '.join(disease_names)} 위험 신호가 있어 오늘은 혈압·혈당 기록을 확인해 주세요.")
        else:
            parts.append("오늘은 건강 기록을 한 번 입력하고, 가벼운 걷기부터 실천해 보세요.")

        if metric.get("obesity", {}).get("status") in {"CAUTION", "HIGH"}:
            parts.append("체중 관리를 위해 야식과 단 음료를 줄이고 식후 10분 걷기를 권장합니다.")
        if metric.get("dyslipidemia", {}).get("status") in {"CAUTION", "HIGH"}:
            parts.append("지질 수치 관리를 위해 튀김·가공식품 섭취를 줄여보세요.")

        today_records = context.get("today_records", {})
        manual_generation_no = context.get("manual_generation_no", 1)
        if today_records.get("vitals"):
            parts.append("오늘 입력한 혈압·혈당 기록을 기준으로 수치 변화를 확인했습니다.")
        else:
            parts.append("오늘 혈압 또는 혈당 기록을 입력하면 조언 정확도가 높아집니다.")
        if today_records.get("exercise_minutes", 0) < 30:
            parts.append("오늘은 30분 걷기나 가벼운 운동을 우선 목표로 잡아보세요.")
        if today_records.get("meals"):
            parts.append("오늘 식단 기록을 기준으로 저염·저당 선택을 이어가 보세요.")

        if manual_generation_no == 2:
            parts.append("두 번째 조언에서는 오늘 남은 시간 동안 가장 실천하기 쉬운 한 가지부터 선택해 보세요.")

        shingles = AdviceService._shingles_vaccination_advice(context)
        if shingles:
            parts.append(shingles)

        parts.append("본 조언은 진단이 아니며, 증상이나 우려가 있으면 전문의와 상담하세요.")
        return AdviceService._limit_text(" ".join(parts), MAX_ADVICE_LENGTH)

    @staticmethod
    async def _latest_today_record_at(user_id: int, today: date):
        latest_vital = (
            await VitalRecord.filter(user_id=user_id, record_date=today).order_by("-updated_at", "-created_at").first()
        )
        latest_activity = (
            await ActivityLog.filter(user_id=user_id, record_date=today).order_by("-updated_at", "-created_at").first()
        )
        latest_exercise = (
            await ExerciseLog.filter(user_id=user_id, exercise_date=today)
            .order_by("-updated_at", "-created_at")
            .first()
        )
        latest_meal = await MealLog.filter(user_id=user_id, meal_date=today).order_by("-created_at").first()
        datetimes = [
            value
            for value in [
                latest_vital.updated_at if latest_vital else None,
                latest_activity.updated_at if latest_activity else None,
                latest_exercise.updated_at if latest_exercise else None,
                latest_meal.created_at if latest_meal else None,
            ]
            if value is not None
        ]
        return max(datetimes) if datetimes else None

    @staticmethod
    def _shingles_vaccination_advice(context: dict[str, Any]) -> str | None:
        age = context.get("age")
        diagnoses = set(context.get("diagnosed_diseases", []))
        chronic_risk = bool(diagnoses.intersection({"DIABETES", "HYPERTENSION"}))
        if age is not None and age >= 65 and chronic_risk:
            return "65세 이상이고 만성질환 이력이 있어 대상포진 예방접종 상담도 고려해 보세요."
        return None

    @staticmethod
    def _prompt_summary(context: dict[str, Any]) -> str:
        at_risk = AdviceService._disease_names(context.get("at_risk_diseases", []))
        generation_no = context.get("manual_generation_no")
        suffix = f" / 수동 생성 {generation_no}회차" if generation_no else ""
        if at_risk:
            return f"위험 신호: {', '.join(at_risk)}{suffix}"
        return f"위험 신호 없음 또는 예측 결과 없음{suffix}"

    @staticmethod
    async def _generate_llm_advice(context: dict[str, Any]) -> AdviceLLMResult | None:
        if not config.ADVICE_LLM_ENABLED:
            return None

        client = OpenAIAdviceClient(
            api_key=config.OPENAI_API_KEY,
            model_name=config.OPENAI_MODEL,
            timeout_seconds=config.OPENAI_TIMEOUT_SECONDS,
        )
        if not client.is_configured:
            return None

        try:
            result = await client.generate(
                context=context,
                prompt_summary=AdviceService._prompt_summary(context),
                max_length=MAX_ADVICE_LENGTH,
            )
        except AdviceLLMError:
            return None

        return AdviceLLMResult(
            advice_text=AdviceService._finalize_llm_advice(result.advice_text),
            provider=result.provider,
            model_name=result.model_name,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cache_read_tokens=result.cache_read_tokens,
        )

    @staticmethod
    def _disease_names(disease_codes: list[str]) -> list[str]:
        labels = {
            "DIABETES": "당뇨",
            "HYPERTENSION": "고혈압",
            "CKD": "만성신장질환",
        }
        return [labels.get(code, code) for code in disease_codes]

    @staticmethod
    def _limit_text(text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _finalize_llm_advice(text: str) -> str:
        normalized = " ".join(text.split())
        has_disclaimer = "진단" in normalized or "전문의" in normalized or "의료" in normalized
        if not has_disclaimer:
            normalized = f"{normalized} {ADVICE_DISCLAIMER}"
        return AdviceService._limit_text(normalized, MAX_ADVICE_LENGTH)

    @staticmethod
    def _to_response(
        advice: LLMAdvice,
        generated: bool,
        remaining_regeneration_count: int = 0,
    ) -> DailyAdviceResponse:
        return DailyAdviceResponse(
            advice_id=advice.id,
            advice_date=advice.advice_date,
            title=ADVICE_TITLE,
            advice_text=advice.advice_text,
            provider=advice.provider,
            model_name=advice.model_name,
            trigger_type=AdviceTriggerType(advice.trigger_type),
            generated=generated,
            created_at=advice.created_at,
            source_type="LLM" if advice.provider == OPENAI_PROVIDER else "RULE_BASED",
            remaining_regeneration_count=remaining_regeneration_count,
        )

    @staticmethod
    def _to_history_item(advice: LLMAdvice, feedback: AdviceFeedback | None) -> AdviceHistoryItemResponse:
        return AdviceHistoryItemResponse(
            advice_id=advice.id,
            advice_date=advice.advice_date,
            title=ADVICE_TITLE,
            advice_text=advice.advice_text,
            trigger_type=AdviceTriggerType(advice.trigger_type),
            source_type="LLM" if advice.provider == OPENAI_PROVIDER else "RULE_BASED",
            feedback_type=AdviceFeedbackType(feedback.feedback_type) if feedback else None,
            created_at=advice.created_at,
        )

    @staticmethod
    def _to_feedback_response(feedback: AdviceFeedback, advice_id: int) -> AdviceFeedbackCreateResponse:
        return AdviceFeedbackCreateResponse(
            feedback_id=feedback.id,
            advice_id=advice_id,
            feedback_type=AdviceFeedbackType(feedback.feedback_type),
            created_at=feedback.created_at,
        )
