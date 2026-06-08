from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions import register_exception_handlers


class SampleRequest(BaseModel):
    count: int


def create_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/conflict")
    async def conflict():
        raise HTTPException(status_code=409, detail="이미 처리된 요청입니다.")

    @app.post("/samples")
    async def create_sample(request: SampleRequest):
        return request

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
