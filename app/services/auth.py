import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi.exceptions import HTTPException
from pydantic import EmailStr
from starlette import status
from tortoise.transactions import in_transaction

from app.core import config, default_logger
from app.core.jwt.tokens import AccessToken, RefreshToken
from app.core.utils.common import normalize_phone_number
from app.core.utils.security import hash_password, verify_password
from app.dtos.auth import GoogleRegistrationRequest, LoginRequest, SignUpAvailabilityRequest, SignUpRequest
from app.models.users import ConsentType, EmailVerification, PasswordResetToken, User, UserConsent
from app.repositories.user_repository import UserRepository
from app.services.account_stats import ensure_user_account_stats
from app.services.email import EmailService
from app.services.google_auth import GoogleAuthService
from app.services.jwt import JwtService
from app.services.managed_diseases import replace_user_managed_diseases
from app.services.rate_limiter import AuthRateLimiter
from app.services.refresh_tokens import RefreshTokenSessionService


def _mask_email(email: str) -> str:
    local, sep, domain = email.partition("@")
    if not sep:
        return "***"
    return f"{local[:2]}***@{domain}"


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.jwt_service = JwtService()
        self.rate_limiter = AuthRateLimiter()
        self.email_service = EmailService()
        self.google_auth_service = GoogleAuthService()
        self.refresh_token_sessions = RefreshTokenSessionService()

    async def signup(self, data: SignUpRequest) -> User:
        # 이메일 중복 체크
        await self.check_email_exists(data.email)

        # 입력받은 휴대폰 번호를 노말라이즈
        normalized_phone_number = normalize_phone_number(data.phone_number)

        # 휴대폰 번호 중복 체크
        await self.check_phone_number_exists(normalized_phone_number)

        # 유저 생성
        async with in_transaction():
            user = await self.user_repo.create_user(
                email=data.email,
                hashed_password=hash_password(data.password),  # 해시화된 비밀번호를 사용
                name=data.name,
                phone_number=normalized_phone_number,
                gender=data.gender,
                birthday=data.birth_date,
            )
            await replace_user_managed_diseases(user.id, data.managed_diseases)
            await ensure_user_account_stats(user.id)
            await self._create_initial_consents(user, data)

            return user

    async def check_signup_availability(self, data: SignUpAvailabilityRequest) -> None:
        await self.check_email_exists(data.email)
        await self.check_phone_number_exists(normalize_phone_number(data.phone_number))

    async def authenticate(self, data: LoginRequest, client_ip: str) -> User:
        # 이메일로 사용자 조회
        email = str(data.email)
        await self.rate_limiter.check_login_allowed(email=email, client_ip=client_ip)

        user = await self.user_repo.get_user_by_email(email)
        if not user:
            remaining = await self.rate_limiter.record_login_failure(email=email, client_ip=client_ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이메일 또는 비밀번호가 올바르지 않습니다. ({remaining}회 시도 남음)",
            )

        # 비밀번호 검증
        if not verify_password(data.password, user.hashed_password):
            remaining = await self.rate_limiter.record_login_failure(email=email, client_ip=client_ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이메일 또는 비밀번호가 올바르지 않습니다. ({remaining}회 시도 남음)",
            )

        # 활성 사용자 체크
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="비활성화된 계정입니다.")

        await self.rate_limiter.reset_login_failures(email=email)
        return user

    async def login(self, user: User, remember_me: bool = False) -> dict[str, AccessToken | RefreshToken]:
        await self.user_repo.update_last_login(user.id)
        tokens = self.jwt_service.issue_jwt_pair(user)
        await self.refresh_token_sessions.create_session(user.id, tokens["refresh_token"], remember_me)
        return tokens

    async def authenticate_google(self, id_token: str) -> User:
        google_user = self.google_auth_service.verify_id_token(id_token)
        if not google_user.email_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증되지 않은 Google 이메일입니다.")

        linked_user = await self.user_repo.get_user_by_google_sub(google_user.sub)
        if linked_user:
            if not linked_user.is_active:
                raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="비활성화된 계정입니다.")
            return linked_user

        user = await self.user_repo.get_user_by_email(google_user.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 이메일로 가입된 계정입니다. 일반 로그인으로 이용해 주세요.",
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 Google 이메일로 가입된 계정이 없습니다. 먼저 회원가입을 완료해 주세요.",
        )

    async def signup_google(self, data: GoogleRegistrationRequest) -> User:
        google_user = self.google_auth_service.verify_id_token(data.id_token)
        if not google_user.email_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증되지 않은 Google 이메일입니다.")

        if await self.user_repo.get_user_by_google_sub(google_user.sub):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 연결된 Google 계정입니다.")
        if await self.user_repo.exists_by_email(google_user.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 가입된 이메일입니다.")

        normalized_phone_number = normalize_phone_number(data.phone_number)
        await self.check_phone_number_exists(normalized_phone_number)

        async with in_transaction():
            user = await self.user_repo.create_user(
                email=google_user.email,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                name=data.name or google_user.name or google_user.email.split("@")[0],
                phone_number=normalized_phone_number,
                gender=data.gender,
                birthday=data.birth_date,
                is_email_verified=True,
                auth_provider="GOOGLE",
                google_sub=google_user.sub,
                profile_image_url=google_user.picture,
            )
            await replace_user_managed_diseases(user.id, data.managed_diseases)
            await ensure_user_account_stats(user.id)
            await self._create_initial_consents(user, data)
            return user

    async def request_email_verification(self, user: User) -> None:
        latest = await EmailVerification.filter(user=user, verified_at=None).order_by("-created_at").first()
        if latest and self._is_in_cooldown(latest.created_at, config.EMAIL_VERIFICATION_COOLDOWN_SECONDS):
            self.rate_limiter.raise_limited(config.EMAIL_VERIFICATION_COOLDOWN_SECONDS)

        now = datetime.now(config.TIMEZONE)
        await EmailVerification.filter(user=user, verified_at=None).update(verified_at=now)

        token = self._create_token()
        await EmailVerification.create(
            user=user,
            token_hash=self._hash_token(token),
            expires_at=now + timedelta(hours=config.EMAIL_VERIFICATION_EXPIRE_HOURS),
        )
        await self.email_service.send_email_verification(user=user, token=token)

    async def verify_email(self, token: str) -> None:
        verification = await EmailVerification.get_or_none(token_hash=self._hash_token(token), verified_at=None)
        if not verification:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 토큰입니다.")

        now = datetime.now(config.TIMEZONE)
        if verification.expires_at < now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="토큰이 만료되었습니다. 다시 로그인해주세요.")

        verification.verified_at = now
        await verification.save(update_fields=["verified_at"])
        await self.user_repo.mark_email_verified(verification.user_id)

    async def request_password_reset(self, email: EmailStr) -> None:
        user = await self.user_repo.get_user_by_email(str(email))
        if not user:
            default_logger.info("password reset email skipped: account not found for %s", _mask_email(str(email)))
            return

        latest = await PasswordResetToken.filter(user=user, used_at=None).order_by("-created_at").first()
        if latest and self._is_in_cooldown(latest.created_at, config.PASSWORD_RESET_COOLDOWN_SECONDS):
            self.rate_limiter.raise_limited(config.PASSWORD_RESET_COOLDOWN_SECONDS)

        now = datetime.now(config.TIMEZONE)
        await PasswordResetToken.filter(user=user, used_at=None).update(used_at=now)

        token = self._create_token()
        await PasswordResetToken.create(
            user=user,
            token_hash=self._hash_token(token),
            expires_at=now + timedelta(minutes=config.PASSWORD_RESET_EXPIRE_MINUTES),
        )
        await self.email_service.send_password_reset(user=user, token=token)

    async def reset_password(self, token: str, new_password: str) -> None:
        reset_token = await PasswordResetToken.get_or_none(token_hash=self._hash_token(token), used_at=None)
        if not reset_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 토큰입니다.")

        now = datetime.now(config.TIMEZONE)
        if reset_token.expires_at < now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="토큰이 만료되었습니다. 다시 요청해주세요.")

        await self.user_repo.update_password(reset_token.user_id, hash_password(new_password))
        await self.refresh_token_sessions.revoke_all_for_user(reset_token.user_id)
        reset_token.used_at = now
        await reset_token.save(update_fields=["used_at"])

    async def check_email_exists(self, email: str | EmailStr) -> None:
        if await self.user_repo.exists_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용중인 이메일입니다.")

    async def check_phone_number_exists(self, phone_number: str) -> None:
        if await self.user_repo.exists_by_phone_number(phone_number):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용중인 휴대폰 번호입니다.")

    def _create_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _is_in_cooldown(self, created_at: datetime, cooldown_seconds: int) -> bool:
        return created_at + timedelta(seconds=cooldown_seconds) > datetime.now(config.TIMEZONE)

    @staticmethod
    async def _create_initial_consents(user: User, data: SignUpRequest) -> None:
        now = datetime.now(config.TIMEZONE)
        policy_version = data.consent_terms_version
        consent_rows = [
            UserConsent(
                user=user,
                consent_type=ConsentType.TOS,
                is_agreed=True,
                agreed_at=now,
                policy_version=policy_version,
            ),
            UserConsent(
                user=user,
                consent_type=ConsentType.PRIVACY,
                is_agreed=True,
                agreed_at=now,
                policy_version=policy_version,
            ),
            UserConsent(
                user=user,
                consent_type=ConsentType.HEALTH_DATA,
                is_agreed=True,
                agreed_at=now,
                policy_version=policy_version,
            ),
            UserConsent(
                user=user,
                consent_type=ConsentType.MARKETING,
                is_agreed=data.consent_marketing,
                agreed_at=now if data.consent_marketing else None,
                withdrawn_at=None if data.consent_marketing else now,
                policy_version=policy_version,
            ),
        ]
        await UserConsent.bulk_create(consent_rows)
