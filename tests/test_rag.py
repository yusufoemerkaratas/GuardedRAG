from app.api import routes
from app.schemas.rag import RAGQueryRequest
from app.schemas.retrieval import RetrievalSearchResponse, RetrievalSearchResult
from app.services.rag import FALLBACK_ANSWER, RAGService


class FakeRetrievalService:
    def __init__(self, response: RetrievalSearchResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, int | None]] = []

    def search(self, query: str, top_k: int | None = None) -> RetrievalSearchResponse:
        self.calls.append((query, top_k))
        return self.response


class RecordingAnswerGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[RetrievalSearchResult]]] = []

    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalSearchResult],
    ) -> dict[str, object]:
        self.calls.append((question, context_chunks))
        return {
            "answer": "grounded answer",
            "answerable": True,
            "confidence": 0.91,
            "sources": [
                {
                    "document_id": context_chunks[0].document_id,
                    "chunk_id": context_chunks[0].chunk_id,
                    "chunk_index": context_chunks[0].chunk_index,
                    "page_number": context_chunks[0].page_number,
                    "score": context_chunks[0].score,
                }
            ],
        }


class InvalidAnswerGenerator:
    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalSearchResult],
    ) -> dict[str, str]:
        return {"raw": "unvalidated text"}


class FailingRetrievalService:
    def search(self, query: str, top_k: int | None = None) -> RetrievalSearchResponse:
        raise RuntimeError("retrieval unavailable")


def _retrieval_response(answerable: bool = True) -> RetrievalSearchResponse:
    results = [
        RetrievalSearchResult(
            document_id="doc-1",
            chunk_id="chunk-1",
            chunk_index=0,
            page_number=2,
            text="retrieved source context",
            score=0.91,
        )
    ] if answerable else []
    return RetrievalSearchResponse(
        query="What is in the source?",
        results=results,
        result_count=len(results),
        answerable=answerable,
        similarity_threshold=0.75,
    )


def test_rag_service_retrieves_before_generating_answer() -> None:
    retrieval_service = FakeRetrievalService(_retrieval_response())
    answer_generator = RecordingAnswerGenerator()
    service = RAGService(
        retrieval_service=retrieval_service,
        answer_generator=answer_generator,
    )

    response = service.query(question="What is in the source?", top_k=3)

    assert retrieval_service.calls == [("What is in the source?", 3)]
    assert len(answer_generator.calls) == 1
    assert answer_generator.calls[0][1][0].text == "retrieved source context"
    assert response.answer == "grounded answer"
    assert response.answerable is True
    assert response.confidence == 0.91
    assert response.sources[0].document_id == "doc-1"
    assert response.sources[0].chunk_id == "chunk-1"
    assert response.sources[0].page_number == 2


def test_rag_service_returns_fallback_without_generation_when_unanswerable() -> None:
    retrieval_service = FakeRetrievalService(_retrieval_response(answerable=False))
    answer_generator = RecordingAnswerGenerator()
    service = RAGService(
        retrieval_service=retrieval_service,
        answer_generator=answer_generator,
    )

    response = service.query(question="Unknown?", top_k=5)

    assert retrieval_service.calls == [("Unknown?", 5)]
    assert answer_generator.calls == []
    assert response.answer == FALLBACK_ANSWER
    assert response.answerable is False
    assert response.confidence == 0.0
    assert response.sources == []


def test_rag_service_returns_fallback_when_retrieval_fails() -> None:
    answer_generator = RecordingAnswerGenerator()
    service = RAGService(
        retrieval_service=FailingRetrievalService(),
        answer_generator=answer_generator,
    )

    response = service.query(question="Unknown?", top_k=5)

    assert answer_generator.calls == []
    assert response.answer == FALLBACK_ANSWER
    assert response.answerable is False
    assert response.confidence == 0.0
    assert response.sources == []


def test_rag_service_returns_fallback_for_invalid_generated_answer() -> None:
    service = RAGService(
        retrieval_service=FakeRetrievalService(_retrieval_response()),
        answer_generator=InvalidAnswerGenerator(),
    )

    response = service.query(question="What is in the source?", top_k=3)

    assert response.answer == FALLBACK_ANSWER
    assert response.answerable is False
    assert response.confidence == 0.0
    assert response.sources == []


def test_rag_endpoint_accepts_question(monkeypatch) -> None:
    class FakeRAGService:
        def __init__(self, retrieval_service) -> None:
            self.retrieval_service = retrieval_service

        def query(self, question: str, top_k: int | None = None):
            assert question == "What is in the source?"
            assert top_k == 2
            return RAGService(
                retrieval_service=FakeRetrievalService(_retrieval_response()),
                answer_generator=RecordingAnswerGenerator(),
            ).query(question=question, top_k=top_k)

    monkeypatch.setattr(routes, "RAGService", FakeRAGService)

    response = routes.query_rag(
        RAGQueryRequest(question="What is in the source?", top_k=2)
    )

    assert response.answerable is True
    assert response.sources[0].chunk_id == "chunk-1"


def test_router_includes_rag_query_endpoint() -> None:
    assert any(
        getattr(route, "path", None) == "/rag/query"
        for route in routes.router.routes
    )
