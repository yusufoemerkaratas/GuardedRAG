from __future__ import annotations

from typing import Any, Protocol

from app.core.config import settings


class LLMClientError(Exception):
    """Raised when a language model provider cannot produce a response."""


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class OpenAIResponsesLLMClient:
    def __init__(
        self,
        model: str = settings.chat_model,
        api_key: str | None = settings.openai_api_key,
        timeout_seconds: float = settings.llm_timeout_seconds,
        max_retries: int = settings.llm_max_retries,
        client: Any | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0.")

        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = client or self._build_openai_client()

    def generate(self, prompt: str) -> str:
        if self.client is None:
            raise LLMClientError("OpenAI client is not configured.")

        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                )
                output_text = getattr(response, "output_text", "")
                if not output_text:
                    raise LLMClientError("OpenAI response did not include output text.")
                return output_text
            except Exception as exc:
                last_error = exc

        raise LLMClientError("OpenAI response generation failed.") from last_error

    def _build_openai_client(self) -> Any | None:
        if not self.api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            return None

        return OpenAI(
            api_key=self.api_key,
            timeout=self.timeout_seconds,
            max_retries=self.max_retries,
        )


class MockLLMClient:
    def __init__(self, response_text: str, fail: bool = False) -> None:
        self.response_text = response_text
        self.fail = fail
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.fail:
            raise LLMClientError("Mock LLM failure.")
        return self.response_text
