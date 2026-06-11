import ssl
from dataclasses import dataclass

import certifi
import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, InvalidAudienceError, InvalidIssuerError, PyJWKClientError

from app.core import config


@dataclass(frozen=True)
class GoogleUserInfo:
    sub: str
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None


class GoogleAuthService:
    def verify_id_token(self, id_token: str) -> GoogleUserInfo:
        client_id = (config.GOOGLE_CLIENT_ID or "").strip()
        jwks_url = config.GOOGLE_JWKS_URL.strip()
        issuers = [issuer.strip() for issuer in config.GOOGLE_ISSUERS.split(",") if issuer.strip()]

        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google 로그인 설정이 완료되지 않았습니다.",
            )

        try:
            signing_key = PyJWKClient(
                jwks_url,
                timeout=5,
                ssl_context=ssl.create_default_context(cafile=certifi.where()),
            ).get_signing_key_from_jwt(id_token)
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=issuers,
                leeway=config.JWT_LEEWAY,
            )
        except InvalidAudienceError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Client ID가 일치하지 않습니다. 프론트 VITE_GOOGLE_CLIENT_ID와 백엔드 GOOGLE_CLIENT_ID를 같은 값으로 설정해주세요.",
            ) from exc
        except InvalidIssuerError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google 토큰 발급자 검증에 실패했습니다. GOOGLE_ISSUERS 설정을 확인해주세요.",
            ) from exc
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google 토큰이 만료되었습니다. 다시 로그인해주세요.",
            ) from exc
        except PyJWKClientError as exc:
            reason = str(exc) or "unknown"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google 공개키를 가져오지 못했습니다. 네트워크 또는 GOOGLE_JWKS_URL 설정을 확인해주세요. ({reason})",
            ) from exc
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 Google 토큰입니다."
            ) from exc

        email = str(payload.get("email") or "")
        sub = str(payload.get("sub") or "")
        if not email or not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Google 계정 정보를 확인할 수 없습니다."
            )

        return GoogleUserInfo(
            sub=sub,
            email=email,
            email_verified=bool(payload.get("email_verified")),
            name=payload.get("name"),
            picture=payload.get("picture"),
        )
