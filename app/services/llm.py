from __future__ import annotations

import json
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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


class GitHubModelsLLMClient:
    def __init__(
        self,
        model: str = settings.github_models_model,
        token: str | None = settings.github_models_token,
        base_url: str = settings.github_models_base_url,
        api_version: str = settings.github_models_api_version,
        timeout_seconds: float = settings.llm_timeout_seconds,
        max_retries: int = settings.llm_max_retries,
        opener: Any | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0.")

        self.model = model
        self.token = token
        self.base_url = base_url
        self.api_version = api_version
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.opener = opener or urlopen

    def generate(self, prompt: str) -> str:
        if not self.token:
            raise LLMClientError("GitHub Models token is not configured.")

        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                response_payload = self._post_chat_completion(prompt)
                return _extract_github_models_content(response_payload)
            except (
                HTTPError,
                URLError,
                OSError,
                KeyError,
                IndexError,
                TypeError,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc

        raise LLMClientError("GitHub Models generation failed.") from last_error

    def _post_chat_completion(self, prompt: str) -> dict[str, Any]:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = Request(
            self.base_url,
            data=body,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": self.api_version,
            },
            method="POST",
        )
        with self.opener(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def build_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "github":
        return GitHubModelsLLMClient()
    if provider == "openai":
        return OpenAIResponsesLLMClient()
    raise LLMClientError(f"Unsupported LLM provider: {settings.llm_provider}")


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


def _extract_github_models_content(response_payload: dict[str, Any]) -> str:
    content = response_payload["choices"][0]["message"]["content"]
    if not content:
        raise LLMClientError("GitHub Models response did not include content.")
    return content
