import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_env: str = "development"
    app_name: str = "GuardedRAG API"
    app_version: str = "0.1.0"
    service_name: str = "guardedrag"

    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4.1-mini"

    vector_store_path: Path = Path("data/vector_store")
    top_k: int = Field(default=5, ge=1)
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=200, ge=0)


def _optional_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    return int(raw_value)


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    return float(raw_value)


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_name=os.getenv("APP_NAME", "GuardedRAG API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        service_name=os.getenv("SERVICE_NAME", "guardedrag"),
        openai_api_key=_optional_env("OPENAI_API_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=os.getenv("CHAT_MODEL", "gpt-4.1-mini"),
        vector_store_path=Path(os.getenv("VECTOR_STORE_PATH", "data/vector_store")),
        top_k=_int_env("TOP_K", 5),
        similarity_threshold=_float_env("SIMILARITY_THRESHOLD", 0.75),
        chunk_size=_int_env("CHUNK_SIZE", 1000),
        chunk_overlap=_int_env("CHUNK_OVERLAP", 200),
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()


settings = get_settings()
