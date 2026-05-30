from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from pydantic import ValidationError

from app.schemas.rag import RAGAnswer, RAGQueryResponse, SourceChunk
from app.schemas.retrieval import RetrievalSearchResult
from app.services.llm import LLMClient, LLMClientError, OpenAIResponsesLLMClient
from app.services.prompts import build_context_only_prompt
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
    ) -> Any:
        ...


class ContextOnlyAnswerGenerator:
    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalSearchResult],
    ) -> dict[str, object]:
        context = "\n\n".join(chunk.text for chunk in context_chunks)
        return {
            "answer": f"Based on the retrieved context: {context}",
            "answerable": True,
            "confidence": _confidence_from_sources(context_chunks),
            "sources": _sources_from_results(context_chunks),
        }


class LLMAnswerGenerator:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or OpenAIResponsesLLMClient()

    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalSearchResult],
    ) -> str:
        prompt = build_context_only_prompt(
            question=question,
            context_chunks=context_chunks,
        )
        return self.llm_client.generate(prompt)


class RAGService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        answer_generator: AnswerGenerator | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.answer_generator = answer_generator or LLMAnswerGenerator()

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

        try:
            raw_answer = self.answer_generator.generate(
                question=question,
                context_chunks=retrieval.results,
            )
            structured_answer = RAGAnswer.model_validate(_decode_answer(raw_answer))
        except (json.JSONDecodeError, LLMClientError, ValidationError):
            logger.exception("rag_answer_validation_failed")
            return _fallback_response()

        return RAGQueryResponse(**structured_answer.model_dump())


def _confidence_from_sources(results: list[RetrievalSearchResult]) -> float:
    if not results:
        return 0.0
    return max(0.0, min(1.0, max(result.score for result in results)))


def _decode_answer(raw_answer: Any) -> Any:
    if isinstance(raw_answer, str):
        return json.loads(raw_answer)
    return raw_answer


def _sources_from_results(results: list[RetrievalSearchResult]) -> list[SourceChunk]:
    return [
        SourceChunk(
            document_id=result.document_id,
            chunk_id=result.chunk_id,
            chunk_index=result.chunk_index,
            page_number=result.page_number,
            score=result.score,
        )
        for result in results
    ]


def _fallback_response() -> RAGQueryResponse:
    return RAGQueryResponse(
        answer=FALLBACK_ANSWER,
        answerable=False,
        confidence=0.0,
        sources=[],
    )
