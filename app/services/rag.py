from __future__ import annotations

import logging
from typing import Protocol

from app.schemas.rag import RAGQueryResponse, RAGSource
from app.schemas.retrieval import RetrievalSearchResult
from app.services.retrieval import RetrievalService


FALLBACK_ANSWER = (
    "I could not answer from the indexed sources because no retrieved context "
    "passed the similarity threshold."
)

logger = logging.getLogger(__name__)


class AnswerGenerator(Protocol):
    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalSearchResult],
    ) -> str:
        ...


class ContextOnlyAnswerGenerator:
    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalSearchResult],
    ) -> str:
        context = "\n\n".join(chunk.text for chunk in context_chunks)
        return f"Based on the retrieved context: {context}"


class RAGService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        answer_generator: AnswerGenerator | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.answer_generator = answer_generator or ContextOnlyAnswerGenerator()

    def query(
        self,
        question: str,
        top_k: int | None = None,
    ) -> RAGQueryResponse:
        try:
            retrieval = self.retrieval_service.search(query=question, top_k=top_k)
        except Exception:
            logger.exception("rag_retrieval_failed")
            return _fallback_response()

        if not retrieval.answerable:
            return _fallback_response()

        answer = self.answer_generator.generate(
            question=question,
            context_chunks=retrieval.results,
        )
        return RAGQueryResponse(
            answer=answer,
            answerable=True,
            confidence=_confidence_from_sources(retrieval.results),
            sources=[
                RAGSource(
                    document_id=result.document_id,
                    chunk_id=result.chunk_id,
                    chunk_index=result.chunk_index,
                    page_number=result.page_number,
                    score=result.score,
                )
                for result in retrieval.results
            ],
        )


def _confidence_from_sources(results: list[RetrievalSearchResult]) -> float:
    if not results:
        return 0.0
    return max(0.0, min(1.0, max(result.score for result in results)))


def _fallback_response() -> RAGQueryResponse:
    return RAGQueryResponse(
        answer=FALLBACK_ANSWER,
        answerable=False,
        confidence=0.0,
        sources=[],
    )
