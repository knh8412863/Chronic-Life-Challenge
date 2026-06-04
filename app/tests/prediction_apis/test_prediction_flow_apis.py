from decimal import Decimal
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.services.predictions import PredictionService


class TestPredictionFlowAPIs(TestCase):
    async def test_prediction_flow_returns_three_disease_results_and_missing_input_notice(self):
        signup_data = {
            "email": "prediction@example.com",
            "password": "Password123!",
            "name": "예측테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": "01012341234",
        }
        survey_data = {
            "birth_date": "1990-01-01",
            "height": 165,
            "weight": 63,
            "waist_circumference": 78,
            "smoking_status": 0,
            "alcohol_frequency": 0,
            "exercise_frequency": 3,
            "fh_diabetes_mother": True,
            "walking_days": 4,
            "sedentary_hours": 7.5,
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

            with patch.object(PredictionService, "_run_models", return_value=model_outputs):
                task_response = await client.post(
                    "/api/v1/prediction-tasks",
                    json={"health_input_id": survey_response.json()["data"]["health_input_id"]},
                    headers=headers,
                )

            task_uuid = task_response.json()["data"]["task_uuid"]
            status_response = await client.get(f"/api/v1/prediction-tasks/{task_uuid}/status", headers=headers)
            result_response = await client.get(
                f"/api/v1/prediction-results/{status_response.json()['data']['result_id']}",
                headers=headers,
            )
            feedback_response = await client.post(
                f"/api/v1/prediction-results/{status_response.json()['data']['result_id']}/feedbacks",
                json={
                    "feedback_type": "CORRECT",
                    "actual_diagnosis": {"diabetes": True},
                    "comment": "결과 설명이 이해됐습니다.",
                },
                headers=headers,
            )
            duplicate_feedback_response = await client.post(
                f"/api/v1/prediction-results/{status_response.json()['data']['result_id']}/feedbacks",
                json={"feedback_type": "UNSURE"},
                headers=headers,
            )

        assert survey_response.status_code == status.HTTP_201_CREATED
        assert task_response.status_code == status.HTTP_202_ACCEPTED
        assert task_response.json()["data"]["status"] == "PENDING"
        assert status_response.json()["data"]["status"] == "SUCCESS"
        assert status_response.json()["data"]["progress_percent"] == 100
        assert status_response.json()["data"]["current_step"] == "예측 완료"
        result = result_response.json()["data"]
        assert set(result["disease_risks"]) == {"diabetes", "hypertension", "kidney"}
        assert "당뇨 가족력이 입력되었습니다." in result["disease_risks"]["diabetes"]["risk_factors"]
        assert result["input_completeness"]["used_default_values"] is True
        assert "total_cholesterol" in result["input_completeness"]["missing_fields"]
        assert "waist_circumference" not in result["input_completeness"]["missing_fields"]
        assert feedback_response.status_code == status.HTTP_201_CREATED
        assert feedback_response.json()["data"]["feedback_type"] == "CORRECT"
        assert duplicate_feedback_response.status_code == status.HTTP_409_CONFLICT
