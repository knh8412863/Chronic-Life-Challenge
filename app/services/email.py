from app.core import config, default_logger
from app.core.config import Env
from app.models.users import User


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return f"***{token[-6:]}"


class EmailService:
    async def send_email_verification(self, user: User, token: str) -> None:
        if config.ENV == Env.PROD:
            raise NotImplementedError("Email delivery provider is not configured.")
        default_logger.info(
            "email verification token issued: user_id=%s token_hint=%s token_length=%s",
            user.id,
            _mask_token(token),
            len(token),
        )

    async def send_password_reset(self, user: User, token: str) -> None:
        if config.ENV == Env.PROD:
            raise NotImplementedError("Email delivery provider is not configured.")
        default_logger.info(
            "password reset token issued: user_id=%s token_hint=%s token_length=%s",
            user.id,
            _mask_token(token),
            len(token),
        )
