from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
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


class UserManageService:
    def __init__(self):
        self.repo = UserRepository()

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
        async with in_transaction():
            await UserWithdrawal.create(user_id=user.id, **payload)
            user.is_active = False
            await user.save(update_fields=["is_active", "updated_at"])

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
            content=f"{CONSENT_LABELS[policy_type]} 전문입니다. 실제 운영 시 최신 약관 전문으로 교체합니다.",
        )
