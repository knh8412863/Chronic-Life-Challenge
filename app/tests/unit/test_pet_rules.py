from datetime import datetime
from types import SimpleNamespace

import pytest
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
