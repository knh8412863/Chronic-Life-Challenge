from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.core.utils.common import normalize_phone_number
from app.dtos.users import UserInfoResponse, UserUpdateRequest
from app.models.predictions import ChronicHealthInput, UserProfile
from app.models.users import User
from app.repositories.user_repository import UserRepository


def _calculate_bmi(height_cm: float, weight_kg: float) -> float:
    return round(weight_kg / ((height_cm / 100) ** 2), 2)


def _joined_days(created_at: date, today: date) -> int:
    return max((today - created_at).days + 1, 1)


class UserManageService:
    def __init__(self):
        self.repo = UserRepository()

    async def get_user_info(self, user: User) -> UserInfoResponse:
        profile = await UserProfile.get_or_none(user_id=user.id)
        latest_health = await ChronicHealthInput.filter(user_id=user.id).order_by("-created_at").first()
        return self._to_user_info_response(user=user, profile=profile, latest_health=latest_health, today=date.today())

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
                await self._update_latest_managed_diseases(user.id, data.managed_diseases)
            await user.refresh_from_db()
        return user

    async def update_user_info(self, user: User, data: UserUpdateRequest) -> UserInfoResponse:
        updated_user = await self.update_user(user=user, data=data)
        return await self.get_user_info(updated_user)

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
            managed_diseases=latest_health.diagnosed_diseases if latest_health else [],
            joined_days=_joined_days(user.created_at.date(), today),
            created_at=user.created_at,
        )
