from pathlib import Path

from app.core.config import load_settings


def test_settings_use_safe_defaults(monkeypatch) -> None:
    for name in (
        "OPENAI_API_KEY",
        "GITHUB_MODELS_TOKEN",
        "EMBEDDING_MODEL",
        "CHAT_MODEL",
        "LLM_PROVIDER",
        "LLM_TIMEOUT_SECONDS",
        "LLM_MAX_RETRIES",
        "GITHUB_MODELS_MODEL",
        "GITHUB_MODELS_BASE_URL",
        "GITHUB_MODELS_API_VERSION",
        "VECTOR_STORE_PATH",
        "TOP_K",
        "SIMILARITY_THRESHOLD",
        "CHUNK_SIZE",
        "CHUNK_OVERLAP",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings.openai_api_key is None
    assert settings.github_models_token is None
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.chat_model == "gpt-4.1-mini"
    assert settings.llm_provider == "github"
    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_max_retries == 2
    assert settings.github_models_model == "openai/gpt-4.1"
    assert settings.github_models_base_url == "https://models.github.ai/inference/chat/completions"
    assert settings.github_models_api_version == "2026-03-10"
    assert settings.vector_store_path == Path("data/vector_store")
    assert settings.top_k == 5
    assert settings.similarity_threshold == 0.75
    assert settings.chunk_size == 1000
    assert settings.chunk_overlap == 200


def test_settings_read_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Custom RAG")
    monkeypatch.setenv("APP_VERSION", "2.0.0")
    monkeypatch.setenv("SERVICE_NAME", "custom-service")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "github-token")
    monkeypatch.setenv("EMBEDDING_MODEL", "embedding-test")
    monkeypatch.setenv("CHAT_MODEL", "chat-test")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("LLM_MAX_RETRIES", "4")
    monkeypatch.setenv("GITHUB_MODELS_MODEL", "openai/gpt-4.1-mini")
    monkeypatch.setenv("GITHUB_MODELS_BASE_URL", "https://models.example/inference")
    monkeypatch.setenv("GITHUB_MODELS_API_VERSION", "2026-01-01")
    monkeypatch.setenv("VECTOR_STORE_PATH", "tmp/vector-store")
    monkeypatch.setenv("TOP_K", "8")
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "0.61")
    monkeypatch.setenv("CHUNK_SIZE", "1200")
    monkeypatch.setenv("CHUNK_OVERLAP", "150")

    settings = load_settings()

    assert settings.app_name == "Custom RAG"
    assert settings.app_version == "2.0.0"
    assert settings.service_name == "custom-service"
    assert settings.openai_api_key == "test-key"
    assert settings.github_models_token == "github-token"
    assert settings.embedding_model == "embedding-test"
    assert settings.chat_model == "chat-test"
    assert settings.llm_provider == "openai"
    assert settings.llm_timeout_seconds == 12.5
    assert settings.llm_max_retries == 4
    assert settings.github_models_model == "openai/gpt-4.1-mini"
    assert settings.github_models_base_url == "https://models.example/inference"
    assert settings.github_models_api_version == "2026-01-01"
    assert settings.vector_store_path == Path("tmp/vector-store")
    assert settings.top_k == 8
    assert settings.similarity_threshold == 0.61
    assert settings.chunk_size == 1200
    assert settings.chunk_overlap == 150
