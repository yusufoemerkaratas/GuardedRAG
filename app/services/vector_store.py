from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from app.services.embeddings import ChunkEmbedding


class StoredVector(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    page_number: int | None = None
    text: str
    embedding: list[float]
    dimensions: int = Field(ge=1)


class VectorSearchMatch(StoredVector):
    score: float


class VectorStore(Protocol):
    def upsert_chunks(self, chunks: list[ChunkEmbedding]) -> None:
        ...

    def list_document_vectors(self, document_id: str) -> list[StoredVector]:
        ...

    def search(self, embedding: list[float], top_k: int) -> list[VectorSearchMatch]:
        ...


class SQLiteVectorStore:
    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.database_path = self.store_path / "vectors.sqlite3"
        self._initialize()

    def upsert_chunks(self, chunks: list[ChunkEmbedding]) -> None:
        if not chunks:
            return

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO chunk_vectors (
                    chunk_id,
                    document_id,
                    chunk_index,
                    page_number,
                    text,
                    embedding,
                    dimensions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    document_id = excluded.document_id,
                    chunk_index = excluded.chunk_index,
                    page_number = excluded.page_number,
                    text = excluded.text,
                    embedding = excluded.embedding,
                    dimensions = excluded.dimensions
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.page_number,
                        chunk.text,
                        json.dumps(chunk.embedding),
                        chunk.dimensions,
                    )
                    for chunk in chunks
                ],
            )

    def list_document_vectors(self, document_id: str) -> list[StoredVector]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chunk_id,
                    document_id,
                    chunk_index,
                    page_number,
                    text,
                    embedding,
                    dimensions
                FROM chunk_vectors
                WHERE document_id = ?
                ORDER BY chunk_index
                """,
                (document_id,),
            ).fetchall()

        return [
            StoredVector(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                chunk_index=row["chunk_index"],
                page_number=row["page_number"],
                text=row["text"],
                embedding=json.loads(row["embedding"]),
                dimensions=row["dimensions"],
            )
            for row in rows
        ]

    def search(self, embedding: list[float], top_k: int) -> list[VectorSearchMatch]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chunk_id,
                    document_id,
                    chunk_index,
                    page_number,
                    text,
                    embedding,
                    dimensions
                FROM chunk_vectors
                """
            ).fetchall()

        matches: list[VectorSearchMatch] = []
        for row in rows:
            stored_embedding = json.loads(row["embedding"])
            matches.append(
                VectorSearchMatch(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    chunk_index=row["chunk_index"],
                    page_number=row["page_number"],
                    text=row["text"],
                    embedding=stored_embedding,
                    dimensions=row["dimensions"],
                    score=_cosine_similarity(embedding, stored_embedding),
                )
            )
        return sorted(matches, key=lambda match: match.score, reverse=True)[:top_k]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunk_vectors (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    page_number INTEGER,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    dimensions INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chunk_vectors_document_id
                ON chunk_vectors(document_id)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    shared_dimensions = min(len(left), len(right))
    if shared_dimensions == 0:
        return 0.0

    left_values = left[:shared_dimensions]
    right_values = right[:shared_dimensions]
    dot_product = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = sum(value * value for value in left_values) ** 0.5
    right_norm = sum(value * value for value in right_values) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)
