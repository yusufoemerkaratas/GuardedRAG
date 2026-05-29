from __future__ import annotations

import logging

from app.core.config import settings
from app.schemas.retrieval import RetrievalSearchResponse, RetrievalSearchResult
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService | None = None,
        similarity_threshold: float = settings.similarity_threshold,
    ) -> None:
        if not 0 <= similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1.")

        self.vector_store = vector_store
        self.embedding_service = embedding_service or EmbeddingService()
        self.similarity_threshold = similarity_threshold

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
        scores = [match.score for match in matches]
        logger.info(
            "retrieval_score_distribution",
            extra={
                "result_count": len(scores),
                "max_score": max(scores) if scores else None,
                "min_score": min(scores) if scores else None,
                "similarity_threshold": self.similarity_threshold,
            },
        )
        filtered_matches = [
            match
            for match in matches
            if match.score >= self.similarity_threshold
        ]
        results = [
            RetrievalSearchResult(
                document_id=match.document_id,
                chunk_id=match.chunk_id,
                chunk_index=match.chunk_index,
                page_number=match.page_number,
                text=match.text,
                score=match.score,
            )
            for match in filtered_matches
        ]
        return RetrievalSearchResponse(
            query=query,
            results=results,
            result_count=len(results),
            answerable=bool(results),
            similarity_threshold=self.similarity_threshold,
        )
