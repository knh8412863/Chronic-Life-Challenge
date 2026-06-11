from enum import StrEnum

from tortoise import fields, models


class PetType(StrEnum):
    DOG = "DOG"
    CAT = "CAT"
    RABBIT = "RABBIT"
    CAPYBARA = "CAPYBARA"
    HAMSTER = "HAMSTER"


class PetGrowthStage(StrEnum):
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"


class PetActivityType(StrEnum):
    TASK_COMPLETED = "TASK_COMPLETED"
    CHALLENGE_COMPLETED = "CHALLENGE_COMPLETED"
    STREAK_BONUS = "STREAK_BONUS"
    PET_CREATED = "PET_CREATED"
    NAME_CHANGED = "NAME_CHANGED"


class VirtualPet(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.OneToOneField("models.User", related_name="virtual_pet", on_delete=fields.CASCADE)
    pet_type = fields.CharEnumField(enum_type=PetType, max_length=20)
    pet_name = fields.CharField(max_length=50)
    level = fields.IntField(default=1)
    experience = fields.IntField(default=0)
    next_level_experience = fields.IntField(default=1000)
    growth_stage = fields.CharEnumField(enum_type=PetGrowthStage, max_length=20, default=PetGrowthStage.STAGE_1)
    health_percent = fields.IntField(default=0)
    happiness_percent = fields.IntField(default=0)
    last_updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "virtual_pets"


class VirtualPetActivityLog(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="virtual_pet_activity_logs", on_delete=fields.CASCADE)
    pet = fields.ForeignKeyField("models.VirtualPet", related_name="activity_logs", on_delete=fields.CASCADE)
    activity_type = fields.CharEnumField(enum_type=PetActivityType, max_length=30)
    description = fields.CharField(max_length=255)
    experience_delta = fields.IntField(default=0)
    source_type = fields.CharField(max_length=30, null=True)
    source_id = fields.BigIntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "virtual_pet_activity_logs"
