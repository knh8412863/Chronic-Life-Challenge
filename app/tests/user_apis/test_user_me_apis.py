from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app


class TestUserMeApis(TestCase):
    async def test_get_user_me_success(self):
        # 사용자 등록 및 로그인
        email = "me@example.com"
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "내정보테스터",
            "gender": "FEMALE",
            "birth_date": "1992-02-02",
            "phone_number": "01055556666",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)

            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["access_token"]

            # 내 정보 조회
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == email
        assert response.json()["name"] == "내정보테스터"

    async def test_update_user_me_success(self):
        # 사용자 등록 및 로그인
        email = "update_me@example.com"
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "수정전",
            "gender": "MALE",
            "birth_date": "1990-10-10",
            "phone_number": "01077778888",
        }
        update_data = {"name": "수정후"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)

            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["access_token"]

            # 내 정보 수정
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.patch("/api/v1/users/me", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "수정후"

    async def test_get_user_me_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_change_user_me_password_success(self):
        email = "change_password@example.com"
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "비밀번호변경",
            "gender": "FEMALE",
            "birth_date": "1992-02-02",
            "phone_number": "01055557777",
        }
        change_data = {
            "current_password": "Password123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            response = await client.patch("/api/v1/users/me/password", json=change_data, headers=headers)
            old_password_response = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": "Password123!"}
            )
            new_password_response = await client.post(
                "/api/v1/auth/login", json={"email": email, "password": "NewPassword123!"}
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert old_password_response.status_code == status.HTTP_400_BAD_REQUEST
        assert new_password_response.status_code == status.HTTP_200_OK

    async def test_change_user_me_password_rejects_wrong_current_password(self):
        email = "change_password_wrong@example.com"
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "비밀번호오류",
            "gender": "MALE",
            "birth_date": "1990-10-10",
            "phone_number": "01055558888",
        }
        change_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            response = await client.patch("/api/v1/users/me/password", json=change_data, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_withdraw_user_allows_signup_with_same_email_and_phone_number(self):
        email = "withdraw_rejoin@example.com"
        phone_number = "01088889999"
        signup_data = {
            "email": email,
            "password": "Password123!",
            "name": "탈퇴전",
            "gender": "FEMALE",
            "birth_date": "1992-02-02",
            "phone_number": phone_number,
        }
        withdrawal_data = {
            "password": "Password123!",
            "withdrawal_reason": "NOT_USEFUL",
            "withdrawal_comment": "재가입 테스트",
            "confirm_agreed": True,
        }
        rejoin_data = {
            **signup_data,
            "password": "NewPassword123!",
            "name": "재가입",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            withdrawal_response = await client.request(
                "DELETE", "/api/v1/users/me", json=withdrawal_data, headers=headers
            )
            rejoin_response = await client.post("/api/v1/auth/signup", json=rejoin_data)

        assert withdrawal_response.status_code == status.HTTP_204_NO_CONTENT
        assert rejoin_response.status_code == status.HTTP_201_CREATED
