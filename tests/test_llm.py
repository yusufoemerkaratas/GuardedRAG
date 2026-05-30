import json

import pytest

from app.services import llm
from app.services.llm import (
    GitHubModelsLLMClient,
    LLMClientError,
    MockLLMClient,
    OpenAIResponsesLLMClient,
)


class FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class FakeResponses:
    def __init__(self, output_text: str = '{"answer": "ok"}', failures: int = 0) -> None:
        self.output_text = output_text
        self.failures = failures
        self.calls: list[dict[str, str]] = []

    def create(self, model: str, input: str) -> FakeResponse:
        self.calls.append({"model": model, "input": input})
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("temporary provider failure")
        return FakeResponse(self.output_text)


class FakeOpenAIClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeGitHubModelsOpener:
    def __init__(self, payload: dict | None = None, failures: int = 0) -> None:
        self.payload = payload or {
            "choices": [
                {
                    "message": {
                        "content": '{"answer": "from github models"}',
                    }
                }
            ]
        }
        self.failures = failures
        self.calls = []

    def __call__(self, request, timeout: float):
        self.calls.append(
            {
                "url": request.full_url,
                "headers": dict(request.header_items()),
                "body": json.loads(request.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        if self.failures > 0:
            self.failures -= 1
            raise OSError("temporary provider failure")
        return FakeHTTPResponse(self.payload)


def test_openai_llm_client_generates_text_with_configured_model() -> None:
    responses = FakeResponses(output_text='{"answer": "grounded"}')
    client = OpenAIResponsesLLMClient(
        model="chat-test",
        client=FakeOpenAIClient(responses),
    )

    output = client.generate("prompt text")

    assert output == '{"answer": "grounded"}'
    assert responses.calls == [{"model": "chat-test", "input": "prompt text"}]


def test_openai_llm_client_retries_transient_errors() -> None:
    responses = FakeResponses(output_text='{"answer": "ok"}', failures=1)
    client = OpenAIResponsesLLMClient(
        client=FakeOpenAIClient(responses),
        max_retries=1,
    )

    output = client.generate("prompt text")

    assert output == '{"answer": "ok"}'
    assert len(responses.calls) == 2


def test_openai_llm_client_raises_controlled_error_after_retries() -> None:
    responses = FakeResponses(failures=2)
    client = OpenAIResponsesLLMClient(
        client=FakeOpenAIClient(responses),
        max_retries=1,
    )

    with pytest.raises(LLMClientError, match="generation failed"):
        client.generate("prompt text")


def test_openai_llm_client_requires_configuration() -> None:
    client = OpenAIResponsesLLMClient(api_key=None, client=None)

    with pytest.raises(LLMClientError, match="not configured"):
        client.generate("prompt text")


def test_github_models_llm_client_generates_text_with_configured_model() -> None:
    opener = FakeGitHubModelsOpener()
    client = GitHubModelsLLMClient(
        model="openai/gpt-4.1",
        token="github-token",
        base_url="https://models.github.ai/inference/chat/completions",
        api_version="2026-03-10",
        timeout_seconds=12,
        opener=opener,
    )

    output = client.generate("prompt text")

    assert output == '{"answer": "from github models"}'
    assert opener.calls[0]["url"] == "https://models.github.ai/inference/chat/completions"
    assert opener.calls[0]["headers"]["Authorization"] == "Bearer github-token"
    assert opener.calls[0]["headers"]["X-github-api-version"] == "2026-03-10"
    assert opener.calls[0]["body"] == {
        "model": "openai/gpt-4.1",
        "messages": [{"role": "user", "content": "prompt text"}],
        "response_format": {"type": "json_object"},
    }
    assert opener.calls[0]["timeout"] == 12


def test_github_models_llm_client_retries_transient_errors() -> None:
    opener = FakeGitHubModelsOpener(failures=1)
    client = GitHubModelsLLMClient(
        token="github-token",
        opener=opener,
        max_retries=1,
    )

    output = client.generate("prompt text")

    assert output == '{"answer": "from github models"}'
    assert len(opener.calls) == 2


def test_github_models_llm_client_requires_token() -> None:
    client = GitHubModelsLLMClient(token=None)

    with pytest.raises(LLMClientError, match="token is not configured"):
        client.generate("prompt text")


def test_build_llm_client_uses_github_provider(monkeypatch) -> None:
    monkeypatch.setattr(llm.settings, "llm_provider", "github")

    client = llm.build_llm_client()

    assert isinstance(client, GitHubModelsLLMClient)


def test_mock_llm_client_records_prompts() -> None:
    client = MockLLMClient(response_text='{"answer": "mock"}')

    output = client.generate("prompt text")

    assert output == '{"answer": "mock"}'
    assert client.prompts == ["prompt text"]


def test_mock_llm_client_can_fail() -> None:
    client = MockLLMClient(response_text="", fail=True)

    with pytest.raises(LLMClientError, match="Mock LLM failure"):
        client.generate("prompt text")
