import asyncio
import base64
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core import config, default_logger
from app.core.config import Env
from app.models.users import User


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return f"***{token[-6:]}"


class EmailService:
    async def send_email_verification(self, user: User, token: str) -> None:
        verify_url = self._build_url("/email-verify", {"token": token})
        subject = "[All4Health] 이메일 인증을 완료해 주세요"
        body = (
            f"{user.name}님, All4Health 이메일 인증을 완료해 주세요.\n\n"
            f"인증 링크: {verify_url}\n\n"
            "본인이 요청하지 않았다면 이 메일을 무시해 주세요."
        )
        await self._send_or_log(user.email, subject, body, token)

    async def send_password_reset(self, user: User, token: str) -> None:
        reset_url = self._build_url("/password-reset", {"token": token})
        subject = "[All4Health] 비밀번호 재설정 안내"
        body = (
            f"{user.name}님, 아래 링크에서 비밀번호를 재설정해 주세요.\n\n"
            f"재설정 링크: {reset_url}\n\n"
            "본인이 요청하지 않았다면 이 메일을 무시해 주세요."
        )
        await self._send_or_log(user.email, subject, body, token)

    async def send_email_change_verification(self, user: User, new_email: str, token: str) -> None:
        verify_url = self._build_url("/mypage/edit", {"email_change_token": token})
        subject = "[All4Health] 이메일 변경 인증 안내"
        body = (
            f"{user.name}님, All4Health 계정 이메일 변경을 완료해 주세요.\n\n"
            f"변경할 이메일: {new_email}\n"
            f"인증 링크: {verify_url}\n\n"
            "본인이 요청하지 않았다면 이 메일을 무시해 주세요."
        )
        await self._send_or_log(new_email, subject, body, token)

    async def send_report_export(
        self,
        to_email: str,
        file_name: str,
        content: str,
        content_type: str,
        content_encoding: str,
    ) -> None:
        subject = "[All4Health] 주간 리포트 내보내기 파일"
        body = f"요청하신 주간 리포트 내보내기 파일을 첨부합니다.\n\n파일명: {file_name}"
        await self._send_or_log(
            to_email,
            subject,
            body,
            attachment=EmailAttachment(
                file_name=file_name,
                content=content,
                content_type=content_type,
                content_encoding=content_encoding,
            ),
        )

    async def _send_or_log(
        self,
        to_email: str,
        subject: str,
        body: str,
        token: str | None = None,
        attachment: "EmailAttachment | None" = None,
    ) -> None:
        if not config.SMTP_HOST:
            if config.ENV == Env.PROD:
                raise NotImplementedError("Email delivery provider is not configured.")
            default_logger.info(
                "email delivery skipped: to=%s subject=%s token_hint=%s token_length=%s attachment=%s",
                to_email,
                subject,
                _mask_token(token) if token else None,
                len(token) if token else None,
                attachment.file_name if attachment else None,
            )
            return

        await asyncio.to_thread(self._send_smtp, to_email, subject, body, attachment)

    @staticmethod
    def _send_smtp(to_email: str, subject: str, body: str, attachment: "EmailAttachment | None" = None) -> None:
        message = EmailMessage()
        message["From"] = config.SMTP_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)
        if attachment:
            maintype, _, subtype = attachment.content_type.partition("/")
            if not subtype:
                maintype, subtype = "application", "octet-stream"
            payload = (
                base64.b64decode(attachment.content)
                if attachment.content_encoding == "BASE64"
                else attachment.content.encode("utf-8")
            )
            message.add_attachment(
                payload,
                maintype=maintype,
                subtype=subtype.split(";")[0],
                filename=attachment.file_name,
            )

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
            if config.SMTP_USE_TLS:
                smtp.starttls()
            if config.SMTP_USERNAME and config.SMTP_PASSWORD:
                smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            smtp.send_message(message)
        default_logger.info(
            "email delivered via smtp: to=%s subject=%s attachment=%s", to_email, subject, bool(attachment)
        )

    @staticmethod
    def _build_url(path: str, params: dict[str, str]) -> str:
        base_url = config.FRONTEND_BASE_URL.rstrip("/")
        return f"{base_url}{path}?{urlencode(params)}"


class EmailAttachment:
    def __init__(self, file_name: str, content: str, content_type: str, content_encoding: str) -> None:
        self.file_name = file_name
        self.content = content
        self.content_type = content_type
        self.content_encoding = content_encoding
