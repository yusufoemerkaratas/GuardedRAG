from app.api import routes
from app.schemas.retrieval import RetrievalSearchRequest
from app.services.embeddings import ChunkEmbedding, TextEmbedding
from app.services.retrieval import RetrievalService
from app.services.vector_store import SQLiteVectorStore


class FakeEmbeddingService:
    def embed_texts(self, texts) -> list[TextEmbedding]:
        return [
            TextEmbedding(
                text=text,
                embedding=[1.0, 0.0],
                dimensions=2,
            )
            for text in texts
        ]


def _store_with_chunks(tmp_path) -> SQLiteVectorStore:
    store = SQLiteVectorStore(tmp_path / "vector-store")
    store.upsert_chunks(
        [
            ChunkEmbedding(
                document_id="doc-1",
                chunk_id="chunk-best",
                chunk_index=0,
                page_number=1,
                text="alpha topic",
                embedding=[1.0, 0.0],
                dimensions=2,
            ),
            ChunkEmbedding(
                document_id="doc-2",
                chunk_id="chunk-other",
                chunk_index=1,
                page_number=None,
                text="different topic",
                embedding=[0.0, 1.0],
                dimensions=2,
            ),
        ]
    )
    return store


def test_retrieval_service_returns_top_k_with_scores_and_metadata(tmp_path) -> None:
    store = _store_with_chunks(tmp_path)
    service = RetrievalService(
        vector_store=store,
        embedding_service=FakeEmbeddingService(),
    )

    response = service.search(query="alpha", top_k=1)

    assert response.query == "alpha"
    assert response.result_count == 1
    assert response.results[0].document_id == "doc-1"
    assert response.results[0].chunk_id == "chunk-best"
    assert response.results[0].chunk_index == 0
    assert response.results[0].page_number == 1
    assert response.results[0].text == "alpha topic"
    assert response.results[0].score == 1.0


def test_retrieval_service_returns_clean_empty_response(tmp_path) -> None:
    store = SQLiteVectorStore(tmp_path / "empty-vector-store")
    service = RetrievalService(
        vector_store=store,
        embedding_service=FakeEmbeddingService(),
    )

    response = service.search(query="anything", top_k=5)

    assert response.query == "anything"
    assert response.results == []
    assert response.result_count == 0


def test_retrieval_endpoint_uses_request_top_k(tmp_path, monkeypatch) -> None:
    store = _store_with_chunks(tmp_path)
    monkeypatch.setattr(routes, "VECTOR_STORE", store)
    monkeypatch.setattr(
        routes,
        "RetrievalService",
        lambda vector_store: RetrievalService(
            vector_store=vector_store,
            embedding_service=FakeEmbeddingService(),
        ),
    )

    response = routes.search_retrieval(
        RetrievalSearchRequest(query="alpha", top_k=1)
    )

    assert response.result_count == 1
    assert response.results[0].chunk_id == "chunk-best"


def test_openapi_documents_retrieval_search_endpoint() -> None:
    openapi = routes.router.routes

    assert any(
        getattr(route, "path", None) == "/retrieval/search"
        for route in openapi
    )
