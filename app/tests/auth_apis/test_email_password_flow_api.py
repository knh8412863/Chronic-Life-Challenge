from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.core.utils.security import verify_password
from app.main import app
from app.models.users import User


class TestEmailPasswordFlowAPI(TestCase):
    async def test_email_verification_flow_success(self):
        issued_tokens: list[str] = []

        async def capture_email_verification(*args, **kwargs):
            issued_tokens.append(kwargs["token"])

        signup_data = {
            "email": "email_verify@example.com",
            "password": "Password123!",
            "name": "인증테스터",
            "gender": "MALE",
            "birth_date": "1990-01-01",
            "phone_number": "01033334444",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": signup_data["email"], "password": signup_data["password"]},
            )
            access_token = login_response.json()["access_token"]

            from unittest.mock import patch

            with patch(
                "app.services.email.EmailService.send_email_verification",
                new=capture_email_verification,
            ):
                request_response = await client.post(
                    "/api/v1/auth/email-verification-requests",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

            verify_response = await client.get(f"/api/v1/auth/email-verifications?token={issued_tokens[0]}")

        user = await User.get(email=signup_data["email"])
        assert request_response.status_code == status.HTTP_204_NO_CONTENT
        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.json() == {"data": {"verified": True}}
        assert user.is_email_verified is True

    async def test_password_reset_flow_success(self):
        issued_tokens: list[str] = []

        async def capture_password_reset(*args, **kwargs):
            issued_tokens.append(kwargs["token"])

        signup_data = {
            "email": "password_reset@example.com",
            "password": "Password123!",
            "name": "재설정테스터",
            "gender": "FEMALE",
            "birth_date": "1995-01-01",
            "phone_number": "01044445555",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)

            from unittest.mock import patch

            with patch("app.services.email.EmailService.send_password_reset", new=capture_password_reset):
                request_response = await client.post(
                    "/api/v1/auth/password-reset-requests",
                    json={"email": signup_data["email"]},
                )

            reset_response = await client.post(
                "/api/v1/auth/password-resets",
                json={
                    "token": issued_tokens[0],
                    "new_password": "NewPassword123!",
                    "new_password_confirm": "NewPassword123!",
                },
            )

        user = await User.get(email=signup_data["email"])
        assert request_response.status_code == status.HTTP_204_NO_CONTENT
        assert reset_response.status_code == status.HTTP_204_NO_CONTENT
        assert verify_password("NewPassword123!", user.hashed_password)

    async def test_password_reset_request_hides_unknown_email(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/password-reset-requests",
                json={"email": "unknown@example.com"},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT
