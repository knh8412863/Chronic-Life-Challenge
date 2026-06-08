from dataclasses import dataclass

import httpx

from app.services.llm_advice import OPENAI_CHAT_COMPLETIONS_URL, OPENAI_PROVIDER


class ReportLLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReportLLMResult:
    report_text: str
    provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


class OpenAIReportClient:
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

    async def generate(self, source_summary: dict[str, int], max_length: int) -> ReportLLMResult:
        if not self.is_configured:
            raise ReportLLMError("OpenAI API key is not configured.")
        self._validate_api_key()

        payload = {
            "model": self.model_name,
            "messages": self._messages(source_summary, max_length),
            "temperature": 0.35,
            "max_tokens": 350,
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
            raise ReportLLMError(f"OpenAI weekly report generation failed. status={status_code}") from exc
        except (httpx.HTTPError, UnicodeEncodeError) as exc:
            raise ReportLLMError("OpenAI weekly report generation failed.") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ReportLLMError("OpenAI response is not valid JSON.") from exc
        report_text = self._extract_report_text(data)
        usage = data.get("usage") or {}
        prompt_details = usage.get("prompt_tokens_details") or {}
        return ReportLLMResult(
            report_text=report_text,
            provider=OPENAI_PROVIDER,
            model_name=data.get("model") or self.model_name,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cache_read_tokens=int(prompt_details.get("cached_tokens") or 0),
        )

    @staticmethod
    def _messages(source_summary: dict[str, int], max_length: int) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "너는 만성질환 생활습관 관리 웹서비스의 주간 리포트 작성자다. "
                    "사용자의 한 주 건강기록, 예측, 식단, 운동, 챌린지 실천 현황을 생활습관 점검 관점으로 요약한다. "
                    "의료 진단처럼 단정하지 말고, 다음 주에 실천할 수 있는 방향을 제안한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"주간 원천 데이터 요약: {source_summary}\n"
                    f"조건: {max_length}자 이내, 3~5문장, 한국어, 친절하지만 과장 없이 작성. "
                    "건강 기록이 부족하면 부족한 항목 입력을 권장하고, 마지막에는 의료 진단이 아닌 참고 자료임을 포함."
                ),
            },
        ]

    @staticmethod
    def _extract_report_text(data: dict) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise ReportLLMError("OpenAI response has no choices.")

        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            raise ReportLLMError("OpenAI response content is empty.")
        return content

    def _validate_api_key(self) -> None:
        try:
            self.api_key.encode("ascii")  # type: ignore[union-attr]
        except UnicodeEncodeError as exc:
            raise ReportLLMError("OpenAI API key contains invalid characters.") from exc
