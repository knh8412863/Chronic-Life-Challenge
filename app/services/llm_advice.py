from dataclasses import dataclass
from typing import Any

import httpx

OPENAI_PROVIDER = "OPENAI"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


class AdviceLLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdviceLLMResult:
    advice_text: str
    provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


class OpenAIAdviceClient:
    def __init__(
        self,
        api_key: str | None,
        model_name: str,
        timeout_seconds: float,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate(self, context: dict[str, Any], prompt_summary: str, max_length: int) -> AdviceLLMResult:
        if not self.is_configured:
            raise AdviceLLMError("OpenAI API key is not configured.")
        self._validate_api_key()

        payload = {
            "model": self.model_name,
            "messages": self._messages(context, prompt_summary, max_length),
            "temperature": 0.4,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(OPENAI_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise AdviceLLMError(f"OpenAI advice generation failed. status={status_code}") from exc
        except (httpx.HTTPError, UnicodeEncodeError) as exc:
            raise AdviceLLMError("OpenAI advice generation failed.") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise AdviceLLMError("OpenAI response is not valid JSON.") from exc
        advice_text = self._extract_advice_text(data)
        usage = data.get("usage") or {}
        prompt_details = usage.get("prompt_tokens_details") or {}
        return AdviceLLMResult(
            advice_text=advice_text,
            provider=OPENAI_PROVIDER,
            model_name=data.get("model") or self.model_name,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cache_read_tokens=int(prompt_details.get("cached_tokens") or 0),
        )

    def _validate_api_key(self) -> None:
        try:
            self.api_key.encode("ascii")  # type: ignore[union-attr]
        except UnicodeEncodeError as exc:
            raise AdviceLLMError("OpenAI API key contains invalid characters.") from exc

    @staticmethod
    def _messages(context: dict[str, Any], prompt_summary: str, max_length: int) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "너는 만성질환 생활습관 관리 웹서비스의 건강 조언 작성자다. "
                    "의료 진단처럼 단정하지 말고, 사용자가 오늘 실천할 수 있는 짧은 생활습관 조언을 한국어로 작성한다. "
                    "약 처방, 확정 진단, 과도한 공포 표현은 금지한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"요약: {prompt_summary}\n"
                    f"사용자 건강 컨텍스트: {context}\n"
                    f"조건: {max_length}자 이내, 2~3문장, 마지막에는 필요 시 전문의 상담을 권장하는 문구를 포함."
                ),
            },
        ]

    @staticmethod
    def _extract_advice_text(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise AdviceLLMError("OpenAI response has no choices.")

        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            raise AdviceLLMError("OpenAI response content is empty.")
        return content
