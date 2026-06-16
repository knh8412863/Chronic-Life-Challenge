from datetime import date, datetime, timedelta
from decimal import Decimal

import jwt
from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, PyJWTError
from pydantic import EmailStr, TypeAdapter
from tortoise.transactions import in_transaction

from app.core import config
from app.core.utils.common import normalize_phone_number
from app.core.utils.security import hash_password, verify_password
from app.dtos.users import (
    ConsentUpdateRequest,
    PasswordChangeRequest,
    PolicyChangeResponse,
    PolicyDocumentResponse,
    UserConsentItemResponse,
    UserConsentListResponse,
    UserEmailChangeConfirmRequest,
    UserEmailChangeRequest,
    UserInfoResponse,
    UserPasswordVerificationRequest,
    UserUpdateRequest,
    UserWithdrawalRequest,
)
from app.models.predictions import ChronicHealthInput, UserProfile
from app.models.users import ConsentType, PolicyDocument, User, UserConsent
from app.models.users import UserWithdrawalRequest as UserWithdrawal
from app.repositories.user_repository import UserRepository
from app.services.account_stats import sync_user_account_stats
from app.services.email import EmailService
from app.services.managed_diseases import get_user_managed_disease_codes, replace_user_managed_diseases


def _calculate_bmi(height_cm: float, weight_kg: float) -> float:
    return round(weight_kg / ((height_cm / 100) ** 2), 2)


def _joined_days(created_at: date, today: date) -> int:
    return max((today - created_at).days + 1, 1)


CONSENT_LABELS = {
    ConsentType.TOS: "서비스 이용약관",
    ConsentType.PRIVACY: "개인정보 처리방침",
    ConsentType.HEALTH_DATA: "건강 데이터 수집·이용 동의",
    ConsentType.MARKETING: "마케팅 정보 수신 동의",
    ConsentType.LOCATION: "위치 기반 서비스 이용약관",
}
REQUIRED_CONSENTS = {ConsentType.TOS, ConsentType.PRIVACY, ConsentType.HEALTH_DATA}
CHANGEABLE_CONSENTS = {ConsentType.MARKETING, ConsentType.LOCATION}
DEFAULT_POLICY_CONTENTS = {
    ConsentType.TOS: """제1조 (목적)
본 약관은 ALL4Health가 제공하는 All4Health Chronic Care 서비스의 이용 조건 및 절차, 회사와 회원 간의 권리, 의무 및 책임 사항을 규정함을 목적으로 합니다.

제2조 (이용계약의 성립)
이용계약은 회원이 본 약관에 동의하고 회사가 제시한 회원가입 절차를 완료함으로써 성립합니다.
회사는 서비스의 안정적 제공을 위해 만 14세 미만 아동의 회원가입을 제한할 수 있습니다.

제3조 (서비스의 제공 및 변경)
회사는 회원에게 만성질환 관리, 건강 기록 모니터링, 맞춤형 건강 콘텐츠 제공 등의 서비스를 제공합니다.
본 서비스는 의료법상의 의료행위가 아니며, 서비스 내에서 제공되는 피드백과 정보는 의사의 전문적인 진단이나 치료를 대신할 수 없습니다.

제4조 (회원의 의무 및 탈퇴)
회원은 타인의 정보를 도용하여 가입할 수 없으며, 본인의 건강 데이터를 정확하게 입력해야 합니다.
회원은 언제든지 서비스 내 회원탈퇴 기능을 통해 이용계약을 해지할 수 있으며, 탈퇴 시 관련 법령에 따라 회원 정보가 처리됩니다.""",
    ConsentType.PRIVACY: """수집하는 개인정보 항목
회원가입 시 필수 항목: 이메일 주소, 비밀번호, 이름, 생년월일, 성별, 휴대폰 번호
서비스 이용 과정 생성 정보: 서비스 이용 기록, 접속 로그, 쿠키, 기기 정보

개인정보의 수집 및 이용 목적
이용자 식별 및 본인 확인, 회원제 서비스 제공
만성질환 관리 서비스 고도화 및 시스템 안정성 유지
고객 문의 응대, 고지사항 및 알림 전달

개인정보의 보유 및 이용 기간
회원 탈퇴 시 즉시 파기하는 것을 원칙으로 합니다.
단, 관계 법령에 따라 보존할 필요가 있는 경우 해당 법령에서 정한 기간 동안 안전하게 보관 후 파기합니다.""",
    ConsentType.HEALTH_DATA: """ALL4Health 서비스 제공을 위한 민감정보 처리 동의

수집 및 이용하는 건강정보 항목
회원이 직접 입력한 기저질환 정보, 혈당, 혈압, 신장, 체중, 허리둘레, 지질 지표, 운동 기록, 식단 기록, 생활습관 기록 및 서비스 이용 중 생성된 건강 데이터

수집 및 이용 목적
개인 맞춤형 만성질환 관리 서비스 제공
건강 데이터 모니터링, 추이 분석, 질환 위험 예측, 맞춤형 건강 조언 및 리포트 생성

보유 및 이용 기간
회원 탈퇴 시 즉시 파기

귀하는 본 동의를 거부할 권리가 있습니다.
다만, 본 동의는 만성질환 관리 서비스 제공을 위한 필수 사항이므로 동의를 거부할 경우 서비스 이용이 제한됩니다.""",
    ConsentType.MARKETING: """마케팅 목적 개인정보 이용 및 광고성 정보 수신 동의

수집 및 이용 목적
ALL4Health가 제공하는 신규 서비스 및 기능 안내, 맞춤형 혜택 정보 제공, 건강 관련 이벤트 및 프로모션 안내

수집 항목
이메일 주소, 서비스 이용 기록

보유 및 이용 기간
회원 탈퇴 시 또는 마케팅 동의 철회 시까지

귀하는 본 동의를 거부할 권리가 있으며, 거부하더라도 ALL4Health의 핵심 만성질환 관리 서비스 이용에는 제한이 없습니다.""",
    ConsentType.LOCATION: "현재 위치기반 서비스는 MVP 범위에 포함되지 않습니다.",
}
EMAIL_CHANGE_TOKEN_PURPOSE = "email_change"
EMAIL_CHANGE_EXPIRE_MINUTES = 30


class UserManageService:
    def __init__(self):
        self.repo = UserRepository()
        self.email_service = EmailService()

    async def get_user_info(self, user: User) -> UserInfoResponse:
        profile = await UserProfile.get_or_none(user_id=user.id)
        latest_health = await ChronicHealthInput.filter(user_id=user.id).order_by("-created_at").first()
        managed_diseases = await get_user_managed_disease_codes(user.id)
        if not managed_diseases and latest_health:
            managed_diseases = latest_health.diagnosed_diseases
        account_stats = await sync_user_account_stats(user.id)
        return self._to_user_info_response(
            user=user,
            profile=profile,
            latest_health=latest_health,
            managed_diseases=managed_diseases,
            account_stats=account_stats,
            today=date.today(),
        )

    async def update_user(self, user: User, data: UserUpdateRequest) -> User:
        profile = await UserProfile.get_or_none(user_id=user.id)
        if data.phone_number:
            normalized_phone_number = normalize_phone_number(data.phone_number)
            if normalized_phone_number != user.phone_number and await self.repo.exists_by_phone_number(
                normalized_phone_number
            ):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용중인 휴대폰 번호입니다.")
            data.phone_number = normalized_phone_number

        profile_payload = self._build_profile_update_payload(user, profile, data)
        user_payload = data.model_dump(
            include={"name", "phone_number", "profile_image_url"},
            exclude_none=True,
        )

        async with in_transaction():
            await self.repo.update_instance(user=user, data=user_payload)
            if profile_payload:
                await UserProfile.update_or_create(defaults=profile_payload, user_id=user.id)
            if data.managed_diseases is not None:
                await replace_user_managed_diseases(user.id, data.managed_diseases)
                await self._update_latest_managed_diseases(user.id, data.managed_diseases)
            await user.refresh_from_db()
        return user

    async def update_user_info(self, user: User, data: UserUpdateRequest) -> UserInfoResponse:
        updated_user = await self.update_user(user=user, data=data)
        return await self.get_user_info(updated_user)

    async def verify_current_password(self, user: User, data: UserPasswordVerificationRequest) -> None:
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 올바르지 않습니다.")

    async def request_email_change(self, user: User, data: UserEmailChangeRequest) -> None:
        new_email = str(data.new_email).lower()
        if new_email == user.email.lower():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="현재 이메일과 동일합니다.")
        if await self.repo.exists_by_email(new_email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용중인 이메일입니다.")

        token = self._create_email_change_token(user.id, new_email)
        await self.email_service.send_email_change_verification(user=user, new_email=new_email, token=token)

    async def confirm_email_change(self, user: User, data: UserEmailChangeConfirmRequest) -> UserInfoResponse:
        payload = self._decode_email_change_token(data.token)
        if payload["user_id"] != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이메일 변경 권한이 없습니다.")

        new_email = payload["new_email"]
        if await self.repo.exists_by_email(new_email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용중인 이메일입니다.")

        user.email = new_email
        user.is_email_verified = True
        user.updated_at = datetime.now(config.TIMEZONE)
        await user.save(update_fields=["email", "is_email_verified", "updated_at"])
        return await self.get_user_info(user)

    async def get_consents(self, user: User) -> UserConsentListResponse:
        consent_rows = await UserConsent.filter(user_id=user.id)
        consent_map = {ConsentType(row.consent_type): row for row in consent_rows}
        documents = await PolicyDocument.filter(is_active=True)
        return self._build_consent_list(consent_map, documents)

    async def update_consent(
        self,
        user: User,
        consent_type: ConsentType,
        data: ConsentUpdateRequest,
    ) -> UserConsentItemResponse:
        if consent_type not in CHANGEABLE_CONSENTS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="변경할 수 없는 약관입니다.")

        now = datetime.now(config.TIMEZONE)
        consent, _ = await UserConsent.get_or_create(
            user_id=user.id,
            consent_type=consent_type,
            defaults={
                "is_agreed": data.is_agreed,
                "agreed_at": now if data.is_agreed else None,
                "withdrawn_at": None if data.is_agreed else now,
                "policy_version": data.policy_version,
            },
        )
        if not _:
            consent.is_agreed = data.is_agreed
            consent.agreed_at = now if data.is_agreed else consent.agreed_at
            consent.withdrawn_at = None if data.is_agreed else now
            consent.policy_version = data.policy_version
            await consent.save(update_fields=["is_agreed", "agreed_at", "withdrawn_at", "policy_version", "updated_at"])

        return self._to_consent_item(consent_type, consent)

    async def get_policy_document(
        self,
        policy_type: ConsentType,
        version: str | None = None,
    ) -> PolicyDocumentResponse:
        query = PolicyDocument.filter(policy_type=policy_type)
        if version:
            query = query.filter(policy_version=version)
        else:
            query = query.filter(is_active=True)
        document = await query.order_by("-created_at").first()
        if document:
            return PolicyDocumentResponse(
                policy_type=document.policy_type,
                title=document.title,
                policy_version=document.policy_version,
                changed_at=document.changed_at,
                content=document.content,
            )
        return self._default_policy_document(policy_type, version)

    async def withdraw_user(self, user: User, data: UserWithdrawalRequest) -> None:
        self._validate_withdrawal_agreement(data.confirm_agreed)
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 올바르지 않습니다.")

        payload = self._build_withdrawal_payload(data)
        anonymized_payload = self._build_withdrawn_user_payload(user.id)
        async with in_transaction():
            await UserWithdrawal.create(user_id=user.id, **payload)
            for field, value in anonymized_payload.items():
                setattr(user, field, value)
            await user.save(update_fields=[*anonymized_payload.keys(), "updated_at"])

    async def change_password(self, user: User, data: PasswordChangeRequest) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="현재 비밀번호가 올바르지 않습니다.")
        if verify_password(data.new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="새 비밀번호는 현재 비밀번호와 달라야 합니다.",
            )

        await self.repo.update_password(user.id, hash_password(data.new_password))

    @staticmethod
    def _build_profile_update_payload(
        user: User,
        profile: UserProfile | None,
        data: UserUpdateRequest,
    ) -> dict:
        if data.height is None and data.weight is None:
            return {}

        if profile is None and (data.height is None or data.weight is None):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="키와 몸무게를 함께 입력해주세요."
            )

        height = data.height if data.height is not None else float(profile.height_cm)
        weight = data.weight if data.weight is not None else float(profile.weight_kg)
        return {
            "birth_date": profile.birth_date if profile else user.birthday,
            "gender": profile.gender if profile else user.gender,
            "height_cm": Decimal(str(height)),
            "weight_kg": Decimal(str(weight)),
            "bmi": Decimal(str(_calculate_bmi(height, weight))),
        }

    @staticmethod
    def _create_email_change_token(user_id: int, new_email: str) -> str:
        now = datetime.now(config.TIMEZONE)
        payload = {
            "purpose": EMAIL_CHANGE_TOKEN_PURPOSE,
            "user_id": user_id,
            "new_email": new_email,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=EMAIL_CHANGE_EXPIRE_MINUTES)).timestamp()),
        }
        return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    @staticmethod
    def _decode_email_change_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="이메일 변경 인증 시간이 만료되었습니다."
            ) from exc
        except PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 인증 토큰입니다."
            ) from exc

        if payload.get("purpose") != EMAIL_CHANGE_TOKEN_PURPOSE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 인증 토큰입니다.")
        new_email = payload.get("new_email")
        user_id = payload.get("user_id")
        if not isinstance(new_email, str) or not isinstance(user_id, int):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 인증 토큰입니다.")
        try:
            validated_email = TypeAdapter(EmailStr).validate_python(new_email)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 인증 토큰입니다."
            ) from exc
        return {"user_id": user_id, "new_email": str(validated_email).lower()}

    @staticmethod
    def _validate_withdrawal_agreement(confirm_agreed: bool) -> None:
        if not confirm_agreed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="탈퇴 유의사항에 동의해주세요."
            )

    @staticmethod
    def _build_withdrawal_payload(data: UserWithdrawalRequest) -> dict:
        return {
            "withdrawal_reason": data.withdrawal_reason,
            "withdrawal_comment": data.withdrawal_comment.strip() if data.withdrawal_comment else None,
            "confirm_agreed": data.confirm_agreed,
        }

    @staticmethod
    def _build_withdrawn_user_payload(user_id: int) -> dict:
        return {
            "email": f"withdrawn_{user_id}@all4health.deleted",
            "phone_number": f"WD{user_id:09d}"[-11:],
            "google_sub": None,
            "profile_image_url": None,
            "is_active": False,
        }

    @staticmethod
    async def _update_latest_managed_diseases(user_id: int, managed_diseases: list[str]) -> None:
        latest_health = await ChronicHealthInput.filter(user_id=user_id).order_by("-created_at").first()
        if latest_health is None:
            return
        latest_health.diagnosed_diseases = sorted(set(managed_diseases))
        await latest_health.save(update_fields=["diagnosed_diseases"])

    @staticmethod
    def _to_user_info_response(
        user: User,
        profile: UserProfile | None,
        latest_health: ChronicHealthInput | None,
        managed_diseases: list[str],
        account_stats,
        today: date,
    ) -> UserInfoResponse:
        return UserInfoResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            birthday=user.birthday,
            gender=user.gender,
            profile_image_url=user.profile_image_url,
            height=float(profile.height_cm) if profile else None,
            weight=float(profile.weight_kg) if profile else None,
            bmi=float(profile.bmi) if profile else None,
            managed_diseases=managed_diseases,
            joined_days=_joined_days(user.created_at.date(), today),
            membership_grade=account_stats.membership_grade,
            points=account_stats.points,
            level=account_stats.level,
            created_at=user.created_at,
        )

    @staticmethod
    def _build_consent_list(
        consent_map: dict[ConsentType, UserConsent],
        documents: list[PolicyDocument],
    ) -> UserConsentListResponse:
        items = [
            UserManageService._to_consent_item(consent_type, consent_map.get(consent_type))
            for consent_type in ConsentType
        ]
        recent_changes = [
            PolicyChangeResponse(
                policy_type=document.policy_type,
                title=document.title,
                policy_version=document.policy_version,
                changed_at=document.changed_at,
            )
            for document in documents
            if document.changed_at is not None
        ]
        return UserConsentListResponse(items=items, recent_policy_changes=recent_changes[:5])

    @staticmethod
    def _to_consent_item(
        consent_type: ConsentType,
        consent: UserConsent | None,
    ) -> UserConsentItemResponse:
        is_required = consent_type in REQUIRED_CONSENTS
        return UserConsentItemResponse(
            consent_type=consent_type.value,
            title=CONSENT_LABELS[consent_type],
            is_required=is_required,
            is_agreed=consent.is_agreed if consent else is_required,
            agreed_at=consent.agreed_at if consent else None,
            withdrawn_at=consent.withdrawn_at if consent else None,
            policy_version=consent.policy_version if consent else "v1.0",
        )

    @staticmethod
    def _default_policy_document(policy_type: ConsentType, version: str | None) -> PolicyDocumentResponse:
        return PolicyDocumentResponse(
            policy_type=policy_type.value,
            title=CONSENT_LABELS[policy_type],
            policy_version=version or "v1.0",
            changed_at=None,
            content=DEFAULT_POLICY_CONTENTS[policy_type],
        )
