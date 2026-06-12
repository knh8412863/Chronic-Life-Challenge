from decimal import Decimal
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from ai_worker.main import PredictionWorker
from app.main import app
from app.services.predictions import PredictionService


class TestHomeSummaryAPI(TestCase):
    async def test_home_summary_returns_default_values_before_health_input(self):
        signup_data = {
            "email": "home-empty@example.com",
            "password": "Password123!",
            "name": "홈요약",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": "01011112222",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": signup_data["email"], "password": signup_data["password"]},
            )
            headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
            response = await client.get("/api/v1/home/summary", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()["data"]
        assert result["today_score"]["score"] is None
        assert result["today_score"]["status"] == "NEEDS_INPUT"
        assert result["recent_prediction"] is None
        assert result["quick_record_status"]["has_health_survey"] is False
        assert result["unread_notification_count"] == 0

    async def test_home_summary_returns_recent_prediction_and_record_status(self):
        signup_data = {
            "email": "home-filled@example.com",
            "password": "Password123!",
            "name": "홈요약완료",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": "01033334444",
        }
        survey_data = {
            "birth_date": "1990-01-01",
            "height": 160,
            "weight": 67,
            "waist_circumference": 88,
            "smoking_status": 0,
            "alcohol_frequency": 0,
            "exercise_frequency": 3,
        }
        lipid_data = {
            "record_date": "2026-06-01",
            "total_cholesterol": 230,
            "hdl_cholesterol": 45,
            "ldl_cholesterol": 165,
            "triglycerides": 180,
        }
        model_outputs = {
            "DIABETES": {
                "probability": Decimal("0.120000"),
                "threshold": Decimal("0.05500"),
                "is_at_risk": True,
                "risk_level": "HIGH",
                "message": "당뇨 위험 신호가 감지되었습니다. 전문의와 상담해 보세요.",
            },
            "HYPERTENSION": {
                "probability": Decimal("0.050000"),
                "threshold": Decimal("0.09600"),
                "is_at_risk": False,
                "risk_level": "LOW",
                "message": "고혈압 위험 신호는 현재 기준에서 높지 않습니다.",
            },
            "CKD": {
                "probability": Decimal("0.020000"),
                "threshold": Decimal("0.05900"),
                "is_at_risk": False,
                "risk_level": "LOW",
                "message": "만성신장질환 위험 신호는 현재 기준에서 높지 않습니다.",
            },
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": signup_data["email"], "password": signup_data["password"]},
            )
            headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
            survey_response = await client.post("/api/v1/prediction-inputs", json=survey_data, headers=headers)
            await client.post("/api/v1/health/lipid-obesity-records", json=lipid_data, headers=headers)

            with patch.object(PredictionService, "_run_models", return_value=model_outputs):
                task_response = await client.post(
                    "/api/v1/prediction-tasks",
                    json={"health_input_id": survey_response.json()["data"]["health_input_id"]},
                    headers=headers,
                )
                task_processed = await PredictionWorker().process_once()

            task_uuid = task_response.json()["data"]["task_uuid"]
            await client.get(f"/api/v1/prediction-tasks/{task_uuid}/status", headers=headers)
            response = await client.get("/api/v1/home/summary", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert task_processed is True
        result = response.json()["data"]
        assert result["today_score"]["score"] is not None
        assert result["recent_prediction"]["overall_risk_level"] == "HIGH"
        assert result["recent_prediction"]["at_risk_diseases"] == ["당뇨"]
        assert result["health_metric_summary"]["dyslipidemia"]["status"] == "HIGH"
        assert result["quick_record_status"]["has_health_survey"] is True
        assert result["quick_record_status"]["has_lipid_obesity_record"] is True
