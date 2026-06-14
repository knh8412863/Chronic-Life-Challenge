from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.dtos.pets import VirtualPetCreateRequest, VirtualPetNameUpdateRequest
from app.models.pets import PetActivityType, PetGrowthStage, PetType
from app.services.pets import VirtualPetService


def test_virtual_pet_create_request_trims_name():
    request = VirtualPetCreateRequest(pet_type=PetType.DOG, pet_name="  쿠키  ")

    assert request.pet_name == "쿠키"


def test_virtual_pet_name_rejects_blank_value():
    with pytest.raises(ValidationError):
        VirtualPetNameUpdateRequest(pet_name="   ")


def test_virtual_pet_response_maps_core_status_fields():
    pet = SimpleNamespace(
        id=1,
        pet_type=PetType.CAT,
        pet_name="나비",
        level=5,
        experience=450,
        next_level_experience=1000,
        growth_stage=PetGrowthStage.STAGE_2,
        health_percent=75,
        happiness_percent=60,
    )

    result = VirtualPetService._to_pet_response(pet)

    assert result.pet_id == 1
    assert result.pet_type == PetType.CAT
    assert result.pet_name == "나비"
    assert result.level == 5
    assert result.experience == 450
    assert result.next_level_experience == 1000
    assert result.growth_stage == PetGrowthStage.STAGE_2
    assert result.health_percent == 75
    assert result.happiness_percent == 60


def test_virtual_pet_activity_response_maps_recent_activity():
    created_at = datetime(2026, 6, 4, 8, 30)
    activity = SimpleNamespace(
        activity_type=PetActivityType.PET_CREATED,
        description="쿠키 펫을 선택했습니다.",
        experience_delta=0,
        created_at=created_at,
    )

    result = VirtualPetService._to_activity_response(activity)

    assert result.activity_type == PetActivityType.PET_CREATED
    assert result.description == "쿠키 펫을 선택했습니다."
    assert result.experience_delta == 0
    assert result.created_at == created_at


def test_pet_reward_experience_applies_type_bonus():
    assert VirtualPetService._reward_experience("EXERCISE_30", 50, PetType.DOG) == 60
    assert VirtualPetService._reward_experience("DAILY_HEALTH_LOG", 40, PetType.CAT) == 48
    assert VirtualPetService._reward_experience("VITAL_BP", 30, PetType.RABBIT) == 36
    assert VirtualPetService._reward_experience("WATER_CHALLENGE", 20, PetType.CAPYBARA) == 24
    assert VirtualPetService._reward_experience("VITAL_BP", 30, PetType.DOG) == 30


def test_pet_reward_claim_rejects_when_no_claimable_tasks():
    with pytest.raises(HTTPException) as exc_info:
        VirtualPetService._ensure_claimable_tasks([])

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "수령 가능한 오늘의 펫 보상이 없습니다."


def test_pet_experience_can_level_up_and_update_growth_stage():
    pet = SimpleNamespace(
        level=4,
        experience=950,
        next_level_experience=1000,
        growth_stage=PetGrowthStage.STAGE_1,
    )

    VirtualPetService._apply_experience(pet, 100)

    assert pet.level == 5
    assert pet.experience == 50
    assert pet.next_level_experience == 5000
    assert pet.growth_stage == PetGrowthStage.STAGE_2


def test_pet_growth_stage_uses_level_thresholds():
    assert VirtualPetService._growth_stage(1) == PetGrowthStage.STAGE_1
    assert VirtualPetService._growth_stage(5) == PetGrowthStage.STAGE_2
    assert VirtualPetService._growth_stage(10) == PetGrowthStage.STAGE_3


def test_pet_percent_caps_at_one_hundred():
    assert VirtualPetService._percent(3, 4) == 75
    assert VirtualPetService._percent(10, 4) == 100
    assert VirtualPetService._percent(1, 0) == 0


def test_pet_water_task_accepts_activity_water_amount():
    assert VirtualPetService._water_task_completed(water_checkin_exists=False, water_ml=1999) is False
    assert VirtualPetService._water_task_completed(water_checkin_exists=False, water_ml=2000) is True
    assert VirtualPetService._water_task_completed(water_checkin_exists=True, water_ml=0) is True


def test_pet_catalog_item_unlocks_by_streak_days():
    item = {
        "catalog_id": "PET_RABBIT",
        "pet_type": PetType.RABBIT,
        "display_name": "토끼",
        "required_streak_days": 3,
        "affinity_score": 2,
    }

    locked = VirtualPetService._to_catalog_item(item, current_streak_days=2)
    unlocked = VirtualPetService._to_catalog_item(item, current_streak_days=3)

    assert locked.is_unlocked is False
    assert locked.display_name == "???"
    assert locked.affinity_score is None
    assert unlocked.is_unlocked is True
    assert unlocked.display_name == "토끼"
    assert unlocked.affinity_score == 2


def test_pet_catalog_default_item_is_always_unlocked():
    item = {
        "catalog_id": "PET_CAT",
        "pet_type": PetType.CAT,
        "display_name": "고양이",
        "required_streak_days": 0,
        "affinity_score": 3,
    }

    result = VirtualPetService._to_catalog_item(item, current_streak_days=0)

    assert result.is_unlocked is True
    assert result.unlock_condition == "기본 제공"


def test_pet_unlock_condition_uses_challenge_streak_days():
    assert VirtualPetService._unlock_condition(0) == "기본 제공"
    assert VirtualPetService._unlock_condition(7) == "챌린지 7일 연속 달성"
