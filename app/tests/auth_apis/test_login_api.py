from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app


class TestLoginAPI(TestCase):
    async def test_login_success(self):
        # 먼저 사용자 등록
        signup_data = {
            "email": "login_test@example.com",
            "password": "Password123!",
            "name": "로그인테스터",
            "gender": "FEMALE",
            "birth_date": "1995-05-05",
            "phone_number": "01011112222",
        }
        login_data = {"email": "login_test@example.com", "password": "Password123!"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)

            # 로그인 시도
            response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        # 쿠키 검증 대신 응답 헤더 확인
        assert any("refresh_token" in header for header in response.headers.get_list("set-cookie"))

    async def test_login_invalid_credentials(self):
        login_data = {"email": "nonexistent@example.com", "password": "WrongPassword123!"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/auth/login", json=login_data)

        # AuthService.authenticate 에서 실패 시 HTTP_400_BAD_REQUEST 발생
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_login_remember_me_sets_persistent_refresh_cookie(self):
        signup_data = {
            "email": "remember_test@example.com",
            "password": "Password123!",
            "name": "세션테스터",
            "gender": "FEMALE",
            "birth_date": "1995-05-05",
            "phone_number": "01022223333",
        }
        login_data = {"email": "remember_test@example.com", "password": "Password123!", "remember_me": True}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/signup", json=signup_data)
            response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        assert "Max-Age=604800" in response.headers["set-cookie"]

    async def test_login_rate_limit_after_repeated_failures(self):
        login_data = {"email": "rate_limit_test@example.com", "password": "WrongPassword123!"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            responses = [await client.post("/api/v1/auth/login", json=login_data) for _ in range(5)]

        assert [response.status_code for response in responses[:4]] == [status.HTTP_400_BAD_REQUEST] * 4
        assert responses[-1].status_code == status.HTTP_429_TOO_MANY_REQUESTS

    async def test_logout_clears_refresh_cookie(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/v1/auth/sessions/current")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert "refresh_token" in response.headers["set-cookie"]
        assert "Max-Age=0" in response.headers["set-cookie"]
