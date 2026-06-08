"""Seed local demo data for frontend and Swagger verification.

This script is for local/demo databases only. It recreates data owned by
demo@all4health.local and leaves other users untouched.
"""

import argparse
import asyncio
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from tortoise import Tortoise

from app.core import config
from app.core.db.databases import TORTOISE_ORM
from app.core.utils.security import hash_password
from app.models.advices import LLMAdvice
from app.models.challenges import Challenge, ChallengeCheckin, ChallengeParticipation
from app.models.foods import FoodAnalysisResult, FoodAnalysisStatus
from app.models.notifications import Notification, NotificationPreference
from app.models.pets import PetActivityType, PetGrowthStage, PetType, VirtualPet, VirtualPetActivityLog
from app.models.predictions import (
    ActivityLog,
    ChronicHealthInput,
    ExerciseLog,
    LifestyleInput,
    LipidObesityRecord,
    MealLog,
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
from app.models.reports import WeeklyReport
from app.models.users import ConsentType, Gender, User, UserConsent

DEMO_EMAIL = "demo@all4health.local"
DEMO_PASSWORD = "Test1234!"
DEMO_NAME = "데모사용자"


def _today() -> date:
    return datetime.now(config.TIMEZONE).date()


def _week_range(today: date) -> tuple[date, date]:
    week_start = today - timedelta(days=today.weekday())
    return week_start, week_start + timedelta(days=6)


async def seed_demo_data(create_schema: bool) -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    if create_schema:
        await Tortoise.generate_schemas(safe=True)

    try:
        user = await _upsert_demo_user()
        await _clear_demo_data(user)
        await _seed_profile_and_health(user)
        await _seed_prediction(user)
        await _seed_food_and_meals(user)
        participation = await _seed_challenges(user)
        await _seed_advice(user)
        await _seed_weekly_report(user)
        await _seed_notifications(user)
        await _seed_pet(user, participation)
    finally:
        await Tortoise.close_connections()

    print("Demo seed data created.")
    print(f"email: {DEMO_EMAIL}")
    print(f"password: {DEMO_PASSWORD}")


async def _upsert_demo_user() -> User:
    user, _ = await User.update_or_create(
        defaults={
            "hashed_password": hash_password(DEMO_PASSWORD),
            "name": DEMO_NAME,
            "gender": Gender.FEMALE,
            "birthday": date(1985, 6, 8),
            "phone_number": "01090000000",
            "is_active": True,
            "is_email_verified": True,
            "is_admin": False,
        },
        email=DEMO_EMAIL,
    )

    now = datetime.now(config.TIMEZONE)
    consent_rows = [
        (ConsentType.TOS, True),
        (ConsentType.PRIVACY, True),
        (ConsentType.HEALTH_DATA, True),
        (ConsentType.MARKETING, False),
    ]
    for consent_type, is_agreed in consent_rows:
        await UserConsent.update_or_create(
            defaults={
                "is_agreed": is_agreed,
                "agreed_at": now if is_agreed else None,
                "withdrawn_at": None if is_agreed else now,
                "policy_version": "v1.0",
            },
            user=user,
            consent_type=consent_type,
        )
    return user


async def _clear_demo_data(user: User) -> None:
    await AdviceFeedbackSafe.delete_for_user(user)
    await LLMAdvice.filter(user_id=user.id).delete()
    await WeeklyReport.filter(user_id=user.id).delete()
    await VirtualPetActivityLog.filter(user_id=user.id).delete()
    await VirtualPet.filter(user_id=user.id).delete()
    await Notification.filter(user_id=user.id).delete()
    await NotificationPreference.filter(user_id=user.id).delete()
    await ChallengeCheckin.filter(user_id=user.id).delete()
    await ChallengeParticipation.filter(user_id=user.id).delete()
    await MealLog.filter(user_id=user.id).delete()
    await FoodAnalysisResult.filter(user_id=user.id).delete()
    await PredictionResultItem.filter(result__user_id=user.id).delete()
    await PredictionResult.filter(user_id=user.id).delete()
    await PredictionTask.filter(user_id=user.id).delete()
    await PredictionInputSnapshot.filter(user_id=user.id).delete()
    await LifestyleInput.filter(user_id=user.id).delete()
    await ChronicHealthInput.filter(user_id=user.id).delete()
    await LipidObesityRecord.filter(user_id=user.id).delete()
    await RenalRecord.filter(user_id=user.id).delete()
    await VitalRecord.filter(user_id=user.id).delete()
    await ActivityLog.filter(user_id=user.id).delete()
    await ExerciseLog.filter(user_id=user.id).delete()


class AdviceFeedbackSafe:
    @staticmethod
    async def delete_for_user(user: User) -> None:
        from app.models.advices import AdviceFeedback

        await AdviceFeedback.filter(user_id=user.id).delete()


async def _seed_profile_and_health(user: User) -> None:
    today = _today()
    height = Decimal("164.0")
    weight = Decimal("63.0")
    bmi = Decimal("23.42")
    await UserProfile.update_or_create(
        defaults={
            "birth_date": user.birthday,
            "gender": user.gender,
            "height_cm": height,
            "weight_kg": weight,
            "bmi": bmi,
        },
        user_id=user.id,
    )
    await UserChronicDiseaseGoal.update_or_create(
        defaults={
            "target_systolic_bp": 125,
            "target_diastolic_bp": 80,
            "target_fasting_glucose": 100,
            "target_postprandial_glucose": 140,
            "target_hba1c": Decimal("6.50"),
            "target_ldl_cholesterol": 100,
            "target_hdl_cholesterol": 60,
            "target_triglycerides": 150,
            "target_bmi": Decimal("23.00"),
            "target_weight_kg": Decimal("60.00"),
            "target_egfr": Decimal("90.00"),
        },
        user_id=user.id,
    )
    await UserLifestyleGoal.update_or_create(
        defaults={
            "target_steps": 9000,
            "target_water_ml": 2000,
            "target_exercise_minutes": 30,
            "target_sleep_hours": Decimal("7.0"),
            "target_diet_score": Decimal("8.0"),
        },
        user_id=user.id,
    )
    health = await ChronicHealthInput.create(
        user=user,
        age=today.year - user.birthday.year,
        gender=user.gender,
        height=height,
        weight=weight,
        bmi=bmi,
        waist_circumference=Decimal("78.0"),
        sbp=132,
        dbp=84,
        glucose_fasting=108,
        diagnosed_diseases=["HYPERTENSION"],
        medications=["HYPERTENSION"],
        last_checkup_period="WITHIN_1_YEAR",
        fh_diabetes_father=False,
        fh_diabetes_mother=True,
        fh_diabetes_sibling=False,
        fh_hypertension_father=True,
        fh_hypertension_mother=False,
        fh_hypertension_sibling=False,
        family_history_ckd=False,
    )
    lifestyle = await LifestyleInput.create(
        user=user,
        smoking_status=0,
        alcohol_frequency=2,
        alcohol_amount=2,
        walking_days=5,
        sedentary_hours=Decimal("7.5"),
        exercise_frequency=4,
        physical_activity_min=180,
        sleep_hours=Decimal("6.5"),
        stress_level=3,
        diet_score=Decimal("7.0"),
    )
    await PredictionInputSnapshot.create(
        user=user,
        input_mode="DEEP",
        chronic_health_input=health,
        lifestyle_input=lifestyle,
        used_default_values=True,
        missing_fields=["creatinine", "bun"],
    )
    await LipidObesityRecord.create(
        user=user,
        record_date=today,
        total_cholesterol=205,
        hdl_cholesterol=54,
        ldl_cholesterol=122,
        triglycerides=168,
        height_cm=height,
        weight_kg=weight,
        bmi=bmi,
        waist_circumference=Decimal("78.0"),
        memo="데모 지질/비만 기록",
    )
    await RenalRecord.create(
        user=user,
        record_date=today,
        creatinine=Decimal("0.82"),
        egfr=Decimal("92.0"),
        bun=Decimal("13.5"),
        urine_protein_pos=False,
        memo="데모 신장 수치",
    )
    for offset, sbp, dbp, glucose in [(0, 128, 82, 104), (1, 134, 86, 112), (2, 126, 80, 99)]:
        record_date = today - timedelta(days=offset)
        await VitalRecord.create(
            user=user,
            record_date=record_date,
            measured_at=datetime.combine(record_date, time(hour=8, minute=30), tzinfo=config.TIMEZONE),
            measure_type="BLOOD_PRESSURE_GLUCOSE",
            sbp=sbp,
            dbp=dbp,
            glucose=glucose,
            memo="데모 혈압/혈당 기록",
            is_critical=sbp >= 140 or glucose >= 126,
        )
    await ActivityLog.create(
        user=user,
        record_date=today,
        alcohol_frequency=2,
        alcohol_amount=2,
        walking_days=5,
        sedentary_hours=Decimal("7.5"),
        sleep_hours=Decimal("6.5"),
        stress_level=3,
        diet_score=Decimal("7.0"),
        memo="데모 생활습관 기록",
    )
    await ExerciseLog.create(
        user=user,
        exercise_date=today,
        exercise_type="WALKING",
        duration_minutes=35,
        calories_burned=160,
        memo="퇴근 후 빠르게 걷기",
    )


async def _seed_prediction(user: User) -> None:
    snapshot = await PredictionInputSnapshot.filter(user_id=user.id).order_by("-created_at").first()
    task = await PredictionTask.create(
        user=user,
        task_uuid=str(uuid.uuid4()),
        input_snapshot=snapshot,
        prediction_mode=PredictionMode.SCREENING,
        status=PredictionStatus.SUCCESS,
        progress_percent=100,
        current_step="예측 완료",
        started_at=datetime.now(config.TIMEZONE) - timedelta(seconds=4),
        completed_at=datetime.now(config.TIMEZONE),
    )
    result = await PredictionResult.create(
        task=task,
        user=user,
        overall_risk_level="CAUTION",
        lifestyle_priority=["혈압 기록 유지", "나트륨 섭취 줄이기", "주 5일 걷기"],
        input_completeness={
            "used_default_values": True,
            "missing_fields": ["creatinine", "bun"],
            "message": "일부 검사 수치가 없어 일반 기준값을 사용했습니다.",
        },
        inference_ms=820,
        disclaimer="본 결과는 의료 진단이 아닌 참고 지표입니다. 증상이나 우려가 있다면 전문의와 상담해 주세요.",
    )
    for disease_code, probability, threshold, at_risk, level, message in [
        ("DIABETES", Decimal("0.041000"), Decimal("0.05500"), False, "LOW", "당뇨 위험 신호는 높지 않습니다."),
        ("HYPERTENSION", Decimal("0.138000"), Decimal("0.09600"), True, "HIGH", "고혈압 위험 신호가 감지되었습니다."),
        ("CKD", Decimal("0.032000"), Decimal("0.05900"), False, "LOW", "만성신장질환 위험 신호는 높지 않습니다."),
    ]:
        await PredictionResultItem.create(
            result=result,
            disease_code=disease_code,
            model_version="V8-demo",
            probability=probability,
            threshold=threshold,
            threshold_profile=PredictionMode.SCREENING.value,
            is_at_risk=at_risk,
            risk_level=level,
            message=message,
            risk_factors=["혈압", "가족력"] if at_risk else [],
        )


async def _seed_food_and_meals(user: User) -> None:
    today = _today()
    analysis = await FoodAnalysisResult.create(
        user=user,
        task_uuid=str(uuid.uuid4()),
        status=FoodAnalysisStatus.SUCCESS,
        meal_date=today,
        meal_type="LUNCH",
        food_name="현미밥 닭가슴살 샐러드",
        amount="1인분",
        calories=520,
        carbs_g=Decimal("62.0"),
        protein_g=Decimal("34.0"),
        fat_g=Decimal("14.0"),
        sodium_mg=Decimal("780.0"),
        sugar_g=Decimal("8.0"),
        fiber_g=Decimal("7.0"),
        health_score=82,
        risk_flags=["나트륨 주의"],
        advice_text="단백질과 식이섬유는 충분하지만 나트륨 섭취를 조금 줄여보세요.",
    )
    for meal_type, food_name, calories in [
        ("BREAKFAST", "그릭요거트와 견과류", 310),
        ("LUNCH", analysis.food_name, analysis.calories),
        ("DINNER", "두부채소볶음", 430),
    ]:
        await MealLog.create(
            user=user,
            food_analysis_result=analysis if meal_type == "LUNCH" else None,
            meal_date=today,
            meal_type=meal_type,
            food_name=food_name,
            amount="1인분",
            calories=calories,
            carbs_g=Decimal("45.0"),
            protein_g=Decimal("22.0"),
            fat_g=Decimal("12.0"),
            sodium_mg=Decimal("650.0"),
            sugar_g=Decimal("6.0"),
            fiber_g=Decimal("5.0"),
            memo="데모 식단 기록",
        )


async def _seed_challenges(user: User) -> ChallengeParticipation:
    today = _today()
    challenge = await Challenge.filter(title="하루 30분 걷기").first()
    challenge_defaults = {
        "description": "하루 30분 걷기를 7일 동안 실천합니다.",
        "category": "EXERCISE",
        "target_metric": "WALKING_MINUTES",
        "goal_value": 30,
        "duration_days": 7,
        "is_active": True,
    }
    if challenge:
        await Challenge.filter(id=challenge.id).update(**challenge_defaults)
        challenge = await Challenge.get(id=challenge.id)
    else:
        challenge = await Challenge.create(title="하루 30분 걷기", **challenge_defaults)
    participation = await ChallengeParticipation.create(
        user=user,
        challenge=challenge,
        start_date=today - timedelta(days=3),
        end_date=today + timedelta(days=3),
        status="IN_PROGRESS",
        progress_count=4,
    )
    for offset in range(4):
        await ChallengeCheckin.create(
            participation=participation,
            user=user,
            checkin_date=today - timedelta(days=offset),
            note="데모 챌린지 체크인",
        )
    return participation


async def _seed_advice(user: User) -> None:
    today = _today()
    await LLMAdvice.create(
        user=user,
        advice_date=today,
        context_snapshot={
            "at_risk_diseases": ["HYPERTENSION"],
            "metric_assessment": {"dyslipidemia": {"status": "CAUTION"}, "obesity": {"status": "NORMAL"}},
        },
        prompt_summary="위험 신호: 고혈압",
        advice_text="오늘은 혈압을 한 번 더 기록하고, 저녁 식사는 국물 섭취를 줄여보세요. 식후 10분 걷기도 도움이 됩니다.",
        provider="RULE_BASED",
        model_name="daily-advice-rules-v1",
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=0,
        trigger_type="AUTO",
    )


async def _seed_weekly_report(user: User) -> None:
    today = _today()
    week_start, week_end = _week_range(today)
    await WeeklyReport.update_or_create(
        defaults={
            "week_end_date": week_end,
            "status": "AVAILABLE",
            "source_summary": {
                "health_survey_count": 1,
                "lipid_obesity_record_count": 1,
                "renal_record_count": 1,
                "vital_record_count": 3,
                "activity_log_count": 1,
                "exercise_log_count": 1,
                "meal_log_count": 3,
                "prediction_count": 1,
                "at_risk_prediction_count": 1,
                "challenge_checkin_count": 4,
            },
            "summary_cards": [
                {
                    "label": "건강 기록",
                    "value": "5건",
                    "status": "NORMAL",
                    "description": "이번 주 입력된 건강 데이터 수입니다.",
                },
                {
                    "label": "AI 위험 신호",
                    "value": "1건",
                    "status": "HIGH",
                    "description": "위험 신호가 포함된 예측 결과 수입니다.",
                },
                {
                    "label": "식단 기록",
                    "value": "3건",
                    "status": "NORMAL",
                    "description": "이번 주 저장한 식단 기록 수입니다.",
                },
                {
                    "label": "운동 기록",
                    "value": "1건",
                    "status": "NORMAL",
                    "description": "이번 주 저장한 운동 기록 수입니다.",
                },
                {
                    "label": "챌린지",
                    "value": "4회",
                    "status": "NORMAL",
                    "description": "이번 주 챌린지 체크인 횟수입니다.",
                },
            ],
            "metric_summaries": [],
            "trend_summary": {
                "status": "UNAVAILABLE",
                "message": "전주 리포트가 없어 추이 비교는 제공하지 않습니다.",
                "previous_week_report_id": None,
            },
            "challenge_summary": {
                "checkin_count": 4,
                "completion_rate": 57.1,
                "status": "IN_PROGRESS",
                "message": "이번 주 챌린지를 4회 실천했습니다.",
            },
            "report_text": "이번 주에는 건강 기록, 식단, 운동, 챌린지 실천이 모두 확인되었습니다. 고혈압 위험 신호가 있어 혈압 기록과 저염 식단을 꾸준히 이어가 보세요.",
            "provider": "RULE_BASED",
            "model_name": "weekly-report-rules-v1",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
        },
        user_id=user.id,
        week_start_date=week_start,
    )


async def _seed_notifications(user: User) -> None:
    now = datetime.now(config.TIMEZONE)
    await NotificationPreference.update_or_create(user_id=user.id)
    for notification_type, title, message, link_url, is_read in [
        ("PREDICTION", "예측 결과가 준비되었습니다", "고혈압 위험 신호를 확인해 주세요.", "/prediction/result", False),
        ("ADVICE", "오늘의 조언이 도착했습니다", "혈압 기록과 저염 식단 실천을 추천합니다.", "/advices/today", False),
        ("CHALLENGE", "챌린지 체크인을 잊지 마세요", "오늘의 걷기 챌린지를 완료해 보세요.", "/challenges", True),
    ]:
        await Notification.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
            is_read=is_read,
            read_at=now if is_read else None,
        )


async def _seed_pet(user: User, participation: ChallengeParticipation) -> None:
    pet = await VirtualPet.create(
        user=user,
        pet_type=PetType.DOG,
        pet_name="하루",
        level=3,
        experience=460,
        next_level_experience=1000,
        growth_stage=PetGrowthStage.STAGE_2,
        health_percent=78,
        happiness_percent=64,
    )
    await VirtualPetActivityLog.create(
        user=user,
        pet=pet,
        activity_type=PetActivityType.PET_CREATED,
        description="데모 펫이 생성되었습니다.",
        experience_delta=0,
    )
    await VirtualPetActivityLog.create(
        user=user,
        pet=pet,
        activity_type=PetActivityType.TASK_COMPLETED,
        description="오늘의 건강 기록 보상",
        experience_delta=80,
        source_type="HEALTH_RECORD",
    )
    await VirtualPetActivityLog.create(
        user=user,
        pet=pet,
        activity_type=PetActivityType.CHALLENGE_COMPLETED,
        description="걷기 챌린지 체크인 보상",
        experience_delta=120,
        source_type="CHALLENGE_CHECKIN",
        source_id=participation.id,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create local demo data for All4Health.")
    parser.add_argument(
        "--create-schema",
        action="store_true",
        help="Create missing tables from current Tortoise models before seeding. Use for local demo DB only.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(seed_demo_data(create_schema=args.create_schema))
