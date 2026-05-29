from __future__ import annotations

from app.core.config import settings
from app.schemas.retrieval import RetrievalSearchResponse, RetrievalSearchResult
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class RetrievalService:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_service = embedding_service or EmbeddingService()

    def search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> RetrievalSearchResponse:
        limit = top_k or settings.top_k
        query_embedding = self.embedding_service.embed_texts([query])[0]
        matches = self.vector_store.search(
            embedding=query_embedding.embedding,
            top_k=limit,
        )
        results = [
            RetrievalSearchResult(
                document_id=match.document_id,
                chunk_id=match.chunk_id,
                chunk_index=match.chunk_index,
                page_number=match.page_number,
                text=match.text,
                score=match.score,
            )
            for match in matches
        ]
        return RetrievalSearchResponse(
            query=query,
            results=results,
            result_count=len(results),
        )
