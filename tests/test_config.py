from pathlib import Path

from app.core.config import load_settings


def test_settings_use_safe_defaults(monkeypatch) -> None:
    for name in (
        "OPENAI_API_KEY",
        "EMBEDDING_MODEL",
        "CHAT_MODEL",
        "VECTOR_STORE_PATH",
        "TOP_K",
        "SIMILARITY_THRESHOLD",
        "CHUNK_SIZE",
        "CHUNK_OVERLAP",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings.openai_api_key is None
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.chat_model == "gpt-4.1-mini"
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
    monkeypatch.setenv("EMBEDDING_MODEL", "embedding-test")
    monkeypatch.setenv("CHAT_MODEL", "chat-test")
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
    assert settings.embedding_model == "embedding-test"
    assert settings.chat_model == "chat-test"
    assert settings.vector_store_path == Path("tmp/vector-store")
    assert settings.top_k == 8
    assert settings.similarity_threshold == 0.61
    assert settings.chunk_size == 1200
    assert settings.chunk_overlap == 150
