from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from app.core.exceptions import register_exception_handlers


class SampleRequest(BaseModel):
    count: int


class ValueErrorRequest(BaseModel):
    birth_date: str

    @field_validator("birth_date")
    @classmethod
    def reject_value(cls, value: str) -> str:
        raise ValueError("서비스 약관에 따라 만14세 미만은 회원가입이 불가합니다.")


def create_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/conflict")
    async def conflict():
        raise HTTPException(status_code=409, detail="이미 처리된 요청입니다.")

    @app.post("/samples")
    async def create_sample(request: SampleRequest):
        return request

    @app.post("/value-error-samples")
    async def create_value_error_sample(request: ValueErrorRequest):
        return request

    @app.get("/unexpected")
    async def unexpected():
        raise RuntimeError("database password leaked")

    return app


def test_http_exception_response_keeps_detail_and_adds_error_metadata():
    client = TestClient(create_test_app())

    response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "이미 처리된 요청입니다.",
        "error": {
            "code": "CONFLICT",
            "message": "이미 처리된 요청입니다.",
            "status_code": 409,
        },
    }


def test_validation_error_response_keeps_detail_list_and_adds_error_metadata():
    client = TestClient(create_test_app())

    response = client.post("/samples", json={"count": "invalid"})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)
    assert body["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "입력값 형식이 올바르지 않습니다.",
        "status_code": 422,
    }


def test_validation_error_response_serializes_value_error_context():
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.post("/value-error-samples", json={"birth_date": "2025-12-13"})

    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["ctx"]["error"] == "서비스 약관에 따라 만14세 미만은 회원가입이 불가합니다."
    assert body["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "입력값 형식이 올바르지 않습니다.",
        "status_code": 422,
    }


def test_unhandled_exception_response_hides_internal_detail_and_adds_error_metadata():
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "서버 오류가 발생했습니다.",
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "서버 오류가 발생했습니다.",
            "status_code": 500,
        },
    }
