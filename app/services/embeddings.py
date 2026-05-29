from __future__ import annotations

from hashlib import sha256
from typing import Any, Iterable

from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.text_chunker import TextChunk


LOCAL_EMBEDDING_DIMENSIONS = 8
DEFAULT_EMBEDDING_BATCH_SIZE = 100


class TextEmbedding(BaseModel):
    text: str
    embedding: list[float]
    dimensions: int = Field(ge=1)


class ChunkEmbedding(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    text: str
    embedding: list[float]
    dimensions: int = Field(ge=1)


class EmbeddingService:
    def __init__(
        self,
        model: str = settings.embedding_model,
        api_key: str | None = settings.openai_api_key,
        client: Any | None = None,
        batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
        fallback_dimensions: int = LOCAL_EMBEDDING_DIMENSIONS,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0.")
        if fallback_dimensions <= 0:
            raise ValueError("fallback_dimensions must be greater than 0.")

        self.model = model
        self.api_key = api_key
        self.client = client or self._build_openai_client(api_key)
        self.batch_size = batch_size
        self.fallback_dimensions = fallback_dimensions

    def embed_texts(self, texts: Iterable[str]) -> list[TextEmbedding]:
        text_list = list(texts)
        if not text_list:
            return []

        if self.client is None:
            return self._embed_with_local_fallback(text_list)

        try:
            return self._embed_with_client(text_list)
        except Exception:
            return self._embed_with_local_fallback(text_list)

    def embed_chunks(self, chunks: Iterable[TextChunk]) -> list[ChunkEmbedding]:
        chunk_list = list(chunks)
        embeddings = self.embed_texts(chunk.text for chunk in chunk_list)

        return [
            ChunkEmbedding(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                text=chunk.text,
                embedding=embedding.embedding,
                dimensions=embedding.dimensions,
            )
            for chunk, embedding in zip(chunk_list, embeddings)
        ]

    def _embed_with_client(self, texts: list[str]) -> list[TextEmbedding]:
        embeddings: list[TextEmbedding] = []
        for batch in _batched(texts, self.batch_size):
            response = self.client.embeddings.create(model=self.model, input=batch)
            response_embeddings = [
                _extract_embedding(item)
                for item in sorted(
                    response.data,
                    key=lambda item: _extract_index(item),
                )
            ]
            embeddings.extend(
                TextEmbedding(
                    text=text,
                    embedding=embedding,
                    dimensions=len(embedding),
                )
                for text, embedding in zip(batch, response_embeddings)
            )
        return embeddings

    def _embed_with_local_fallback(self, texts: list[str]) -> list[TextEmbedding]:
        return [
            TextEmbedding(
                text=text,
                embedding=_stable_local_embedding(text, self.fallback_dimensions),
                dimensions=self.fallback_dimensions,
            )
            for text in texts
        ]

    def _build_openai_client(self, api_key: str | None) -> Any | None:
        if not api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            return None

        return OpenAI(api_key=api_key)


def _batched(values: list[str], batch_size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), batch_size):
        yield values[start:start + batch_size]


def _stable_local_embedding(text: str, dimensions: int) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [
        round((digest[index % len(digest)] / 127.5) - 1.0, 6)
        for index in range(dimensions)
    ]


def _extract_embedding(item: Any) -> list[float]:
    if isinstance(item, dict):
        return item["embedding"]
    return item.embedding


def _extract_index(item: Any) -> int:
    if isinstance(item, dict):
        return item.get("index", 0)
    return getattr(item, "index", 0)
