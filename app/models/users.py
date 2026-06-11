from enum import StrEnum

from tortoise import fields, models


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class ConsentType(StrEnum):
    TOS = "TOS"
    PRIVACY = "PRIVACY"
    HEALTH_DATA = "HEALTH_DATA"
    MARKETING = "MARKETING"
    LOCATION = "LOCATION"


class WithdrawalReason(StrEnum):
    NOT_USEFUL = "NOT_USEFUL"
    PRIVACY_CONCERN = "PRIVACY_CONCERN"
    HARD_TO_USE = "HARD_TO_USE"
    FOUND_ALTERNATIVE = "FOUND_ALTERNATIVE"
    OTHER = "OTHER"


class User(models.Model):
    id = fields.BigIntField(primary_key=True)
    email = fields.CharField(max_length=40)
    hashed_password = fields.CharField(max_length=128)
    name = fields.CharField(max_length=20)
    gender = fields.CharEnumField(enum_type=Gender)
    birthday = fields.DateField()
    phone_number = fields.CharField(max_length=11)
    profile_image_url = fields.CharField(max_length=500, null=True)
    auth_provider = fields.CharField(max_length=20, default="LOCAL")
    google_sub = fields.CharField(max_length=128, null=True, unique=True)
    is_active = fields.BooleanField(default=True)
    is_email_verified = fields.BooleanField(default=False)
    is_admin = fields.BooleanField(default=False)
    last_login = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"


class EmailVerification(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="email_verifications")
    token_hash = fields.CharField(max_length=64, unique=True)
    expires_at = fields.DatetimeField()
    verified_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "email_verifications"


class PasswordResetToken(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="password_reset_tokens")
    token_hash = fields.CharField(max_length=64, unique=True)
    expires_at = fields.DatetimeField()
    used_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "password_reset_tokens"


class UserConsent(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="consents", on_delete=fields.CASCADE)
    consent_type = fields.CharEnumField(enum_type=ConsentType, max_length=40)
    is_agreed = fields.BooleanField()
    agreed_at = fields.DatetimeField(null=True)
    withdrawn_at = fields.DatetimeField(null=True)
    policy_version = fields.CharField(max_length=20)
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_consents"
        unique_together = (("user", "consent_type"),)


class PolicyDocument(models.Model):
    id = fields.BigIntField(primary_key=True)
    policy_type = fields.CharEnumField(enum_type=ConsentType, max_length=40)
    title = fields.CharField(max_length=100)
    policy_version = fields.CharField(max_length=20)
    content = fields.TextField()
    changed_at = fields.DateField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "policy_documents"
        unique_together = (("policy_type", "policy_version"),)


class UserWithdrawalRequest(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="withdrawal_requests", on_delete=fields.CASCADE)
    withdrawal_reason = fields.CharEnumField(enum_type=WithdrawalReason, max_length=40)
    withdrawal_comment = fields.CharField(max_length=500, null=True)
    confirm_agreed = fields.BooleanField(default=False)
    requested_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_withdrawal_requests"
