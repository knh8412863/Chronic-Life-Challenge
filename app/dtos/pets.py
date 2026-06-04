from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.models.pets import PetGrowthStage, PetType


class VirtualPetCreateRequest(BaseModel):
    pet_type: PetType
    pet_name: Annotated[str, Field(min_length=1, max_length=50)]

    @field_validator("pet_name")
    @classmethod
    def validate_pet_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("펫 이름은 1~50자로 입력해주세요.")
        return stripped


class VirtualPetNameUpdateRequest(BaseModel):
    pet_name: Annotated[str, Field(min_length=1, max_length=50)]

    @field_validator("pet_name")
    @classmethod
    def validate_pet_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("펫 이름은 1~50자로 입력해주세요.")
        return stripped


class VirtualPetResponse(BaseModel):
    pet_id: int
    pet_type: PetType
    pet_name: str
    level: int
    experience: int
    next_level_experience: int
    growth_stage: PetGrowthStage
    health_percent: int
    happiness_percent: int


class VirtualPetCreateResponse(BaseModel):
    pet_id: int
    pet_type: PetType
    pet_name: str
    level: int
    experience: int
    growth_stage: PetGrowthStage


class VirtualPetNameUpdateResponse(BaseModel):
    pet_id: int
    pet_name: str


class PetRewardTaskResponse(BaseModel):
    task_type: str
    title: str
    reward_experience: int
    is_completed: bool


class PetRecentActivityResponse(BaseModel):
    activity_type: str
    description: str
    experience_delta: int
    created_at: datetime


class PetRewardClaimResponse(BaseModel):
    awarded_experience: int
    claimed_task_count: int
    level: int
    experience: int
    next_level_experience: int
    growth_stage: PetGrowthStage


class PetCatalogSummaryResponse(BaseModel):
    total_count: int
    unlocked_count: int
    completion_rate: float


class PetCatalogItemResponse(BaseModel):
    catalog_id: str
    pet_type: PetType
    display_name: str
    is_unlocked: bool
    unlock_condition: str
    affinity_score: int | None = None


class PetCatalogResponse(BaseModel):
    summary: PetCatalogSummaryResponse
    items: list[PetCatalogItemResponse]


class VirtualPetStatusResponse(BaseModel):
    has_pet: bool
    pet: VirtualPetResponse | None = None
    today_tasks: list[PetRewardTaskResponse] = Field(default_factory=list)
    recent_activities: list[PetRecentActivityResponse] = Field(default_factory=list)
