from datetime import datetime, time
from decimal import Decimal
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from ai_worker.main import PredictionWorker
from app.core import config
from app.main import app
from app.models.challenges import Challenge
from app.services.predictions import PredictionService


class TestCoreUserFlow(TestCase):
    async def test_signup_health_prediction_challenge_pet_and_home_flow(self):
        today = datetime.now(config.TIMEZONE).date()
        measured_at = datetime.combine(today, time(hour=8, minute=30))
        signup_data = {
            "email": "core-flow@example.com",
            "password": "Password123!",
            "name": "핵심플로우",
            "gender": "FEMALE",
            "birth_date": "1992-04-12",
            "phone_number": "01055556666",
        }
        survey_data = {
            "birth_date": signup_data["birth_date"],
            "height": 165,
            "weight": 62,
            "waist_circumference": 76,
            "last_checkup_period": "UNDER_1_YEAR",
            "sbp": 118,
            "dbp": 76,
            "glucose_fasting": 92,
            "fh_diabetes_mother": True,
            "smoking_status": 0,
            "alcohol_frequency": 0,
            "walking_days": 5,
            "sedentary_hours": 7,
            "exercise_frequency": 4,
            "physical_activity_min": 180,
            "sleep_hours": 7,
            "stress_level": 2,
            "diet_score": 7,
        }
        model_outputs = {
            "DIABETES": {
                "probability": Decimal("0.130000"),
                "threshold": Decimal("0.05500"),
                "is_at_risk": True,
                "risk_level": "HIGH",
                "message": "당뇨 위험 신호가 감지되었습니다. 전문의와 상담해 보세요.",
            },
            "HYPERTENSION": {
                "probability": Decimal("0.030000"),
                "threshold": Decimal("0.09600"),
                "is_at_risk": False,
                "risk_level": "LOW",
                "message": "고혈압 위험 신호는 현재 기준에서 높지 않습니다.",
            },
            "CKD": {
                "probability": Decimal("0.010000"),
                "threshold": Decimal("0.05900"),
                "is_at_risk": False,
                "risk_level": "LOW",
                "message": "만성신장질환 위험 신호는 현재 기준에서 높지 않습니다.",
            },
        }
        water_challenge = await Challenge.create(
            title="물 2L 마시기",
            description="하루 물 섭취 챌린지",
            category="HYDRATION",
            target_metric="WATER",
            goal_value=1,
            duration_days=7,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": signup_data["email"], "password": signup_data["password"]},
            )
            headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

            user_response = await client.get("/api/v1/users/me", headers=headers)
            survey_response = await client.post("/api/v1/prediction-inputs", json=survey_data, headers=headers)
            vital_response = await client.post(
                "/api/v1/health/vitals",
                json={
                    "measured_at": measured_at.isoformat(),
                    "measure_type": "BP_MORNING",
                    "sbp": 118,
                    "dbp": 76,
                    "memo": "아침 혈압",
                },
                headers=headers,
            )
            activity_response = await client.post(
                "/api/v1/health/activity-logs",
                json={
                    "record_date": today.isoformat(),
                    "walking_days": 5,
                    "sedentary_hours": 7,
                    "sleep_hours": 7,
                    "stress_level": 2,
                    "diet_score": 7,
                },
                headers=headers,
            )
            exercise_response = await client.post(
                "/api/v1/health/exercise-logs",
                json={
                    "exercise_date": today.isoformat(),
                    "exercise_type": "WALKING",
                    "duration_minutes": 40,
                    "calories_burned": 160,
                    "memo": "산책",
                },
                headers=headers,
            )

            with patch.object(PredictionService, "_run_models", return_value=model_outputs):
                task_response = await client.post(
                    "/api/v1/prediction-tasks",
                    json={"health_input_id": survey_response.json()["data"]["health_input_id"]},
                    headers=headers,
                )
                task_processed = await PredictionWorker().process_once()

            task_uuid = task_response.json()["data"]["task_uuid"]
            task_status_response = await client.get(f"/api/v1/prediction-tasks/{task_uuid}/status", headers=headers)
            result_id = task_status_response.json()["data"]["result_id"]
            prediction_result_response = await client.get(f"/api/v1/prediction-results/{result_id}", headers=headers)

            join_response = await client.post(
                f"/api/v1/challenges/{water_challenge.id}/participations",
                headers=headers,
            )
            checkin_response = await client.post(
                f"/api/v1/challenge-participations/{join_response.json()['data']['participation_id']}/checkins/today",
                json={"note": "물 챌린지 완료"},
                headers=headers,
            )
            challenge_summary_response = await client.get("/api/v1/challenges/summary", headers=headers)

            pet_create_response = await client.post(
                "/api/v1/virtual-pets",
                json={"pet_type": "DOG", "pet_name": "쿠키"},
                headers=headers,
            )
            pet_status_response = await client.get("/api/v1/virtual-pets", headers=headers)
            pet_reward_response = await client.post("/api/v1/virtual-pets/reward-tasks/claims", headers=headers)
            pet_catalog_response = await client.get("/api/v1/virtual-pets/catalog?pet_type=DOG", headers=headers)
            home_response = await client.get("/api/v1/home/summary", headers=headers)

        assert signup_response.status_code == status.HTTP_201_CREATED
        assert login_response.status_code == status.HTTP_200_OK
        assert user_response.status_code == status.HTTP_200_OK
        assert user_response.json()["email"] == signup_data["email"]

        assert survey_response.status_code == status.HTTP_201_CREATED
        assert vital_response.status_code == status.HTTP_201_CREATED
        assert activity_response.status_code == status.HTTP_201_CREATED
        assert exercise_response.status_code == status.HTTP_201_CREATED

        assert task_response.status_code == status.HTTP_202_ACCEPTED
        assert task_processed is True
        assert task_status_response.json()["data"]["status"] == "SUCCESS"
        assert prediction_result_response.status_code == status.HTTP_200_OK
        assert prediction_result_response.json()["data"]["disease_risks"]["diabetes"]["is_at_risk"] is True

        assert join_response.status_code == status.HTTP_201_CREATED
        assert checkin_response.status_code == status.HTTP_201_CREATED
        assert challenge_summary_response.status_code == status.HTTP_200_OK
        assert challenge_summary_response.json()["data"]["active_count"] == 1

        assert pet_create_response.status_code == status.HTTP_201_CREATED
        assert pet_status_response.status_code == status.HTTP_200_OK
        assert pet_status_response.json()["data"]["has_pet"] is True
        assert pet_reward_response.status_code == status.HTTP_200_OK
        assert pet_reward_response.json()["data"]["claimed_task_count"] >= 3
        assert pet_catalog_response.status_code == status.HTTP_200_OK
        assert pet_catalog_response.json()["data"]["summary"]["total_count"] > 0

        assert home_response.status_code == status.HTTP_200_OK
        assert home_response.json()["data"]["recent_prediction"]["result_id"] == result_id
        assert home_response.json()["data"]["challenge_summary"]["active_count"] == 1
