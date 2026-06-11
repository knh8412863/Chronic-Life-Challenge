from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.google_auth import GoogleAuthService


def test_google_auth_rejects_missing_client_id(monkeypatch):
    monkeypatch.setattr("app.services.google_auth.config.GOOGLE_CLIENT_ID", None)

    with pytest.raises(HTTPException) as exc:
        GoogleAuthService().verify_id_token("id-token")

    assert exc.value.status_code == 503


def test_google_auth_verifies_id_token(monkeypatch):
    class FakeJWKClient:
        def __init__(self, url: str, timeout: int = 30, ssl_context: object | None = None) -> None:
            self.url = url
            self.timeout = timeout
            self.ssl_context = ssl_context

        def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
            assert token == "id-token"
            return SimpleNamespace(key="public-key")

    def fake_decode(
        token: str,
        key: str,
        algorithms: list[str],
        audience: str,
        issuer: list[str],
        leeway: int,
    ) -> dict[str, str | bool]:
        assert token == "id-token"
        assert key == "public-key"
        assert algorithms == ["RS256"]
        assert audience == "google-client-id"
        assert issuer == ["https://accounts.google.com", "accounts.google.com"]
        assert leeway == 5
        return {
            "sub": "google-sub-1",
            "email": "user@example.com",
            "email_verified": True,
            "name": "홍길동",
            "picture": "https://example.com/profile.png",
        }

    monkeypatch.setattr("app.services.google_auth.config.GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setattr(
        "app.services.google_auth.config.GOOGLE_ISSUERS",
        "https://accounts.google.com,accounts.google.com",
    )
    monkeypatch.setattr("app.services.google_auth.PyJWKClient", FakeJWKClient)
    monkeypatch.setattr("app.services.google_auth.jwt.decode", fake_decode)

    result = GoogleAuthService().verify_id_token("id-token")

    assert result.sub == "google-sub-1"
    assert result.email == "user@example.com"
    assert result.email_verified is True
    assert result.name == "홍길동"
    assert result.picture == "https://example.com/profile.png"


def test_google_auth_rejects_missing_identity(monkeypatch):
    class FakeJWKClient:
        def __init__(self, url: str, timeout: int = 30, ssl_context: object | None = None) -> None:
            pass

        def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
            return SimpleNamespace(key="public-key")

    monkeypatch.setattr("app.services.google_auth.config.GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setattr("app.services.google_auth.PyJWKClient", FakeJWKClient)
    monkeypatch.setattr("app.services.google_auth.jwt.decode", lambda *args, **kwargs: {"email_verified": True})

    with pytest.raises(HTTPException) as exc:
        GoogleAuthService().verify_id_token("id-token")

    assert exc.value.status_code == 401
