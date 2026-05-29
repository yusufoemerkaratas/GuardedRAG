import pytest

from app.services.embeddings import EmbeddingService
from app.services.text_chunker import TextChunk


class FakeEmbeddingItem:
    def __init__(self, index: int, embedding: list[float]) -> None:
        self.index = index
        self.embedding = embedding


class FakeEmbeddingResponse:
    def __init__(self, data: list[FakeEmbeddingItem]) -> None:
        self.data = data


class FakeEmbeddingsClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def create(self, model: str, input: list[str]) -> FakeEmbeddingResponse:
        self.calls.append(input)
        return FakeEmbeddingResponse(
            data=[
                FakeEmbeddingItem(index=index, embedding=[float(index), float(len(text))])
                for index, text in enumerate(input)
            ]
        )


class FakeClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsClient()


class FailingEmbeddingsClient:
    def create(self, model: str, input: list[str]) -> FakeEmbeddingResponse:
        raise RuntimeError("provider unavailable")


class FailingClient:
    def __init__(self) -> None:
        self.embeddings = FailingEmbeddingsClient()


def test_local_fallback_embeds_texts_with_consistent_dimensions() -> None:
    service = EmbeddingService(client=None, api_key=None, fallback_dimensions=6)

    embeddings = service.embed_texts(["alpha", "beta"])

    assert [embedding.text for embedding in embeddings] == ["alpha", "beta"]
    assert {embedding.dimensions for embedding in embeddings} == {6}
    assert all(len(embedding.embedding) == 6 for embedding in embeddings)
    assert embeddings[0].embedding != embeddings[1].embedding


def test_local_fallback_is_stable_for_same_text() -> None:
    service = EmbeddingService(client=None, api_key=None)

    first = service.embed_texts(["repeat"])[0]
    second = service.embed_texts(["repeat"])[0]

    assert first.embedding == second.embedding


def test_openai_client_batches_embedding_calls() -> None:
    client = FakeClient()
    service = EmbeddingService(client=client, batch_size=2)

    embeddings = service.embed_texts(["a", "bb", "ccc"])

    assert client.embeddings.calls == [["a", "bb"], ["ccc"]]
    assert [embedding.embedding for embedding in embeddings] == [
        [0.0, 1.0],
        [1.0, 2.0],
        [0.0, 3.0],
    ]


def test_embedding_chunks_preserves_chunk_metadata() -> None:
    service = EmbeddingService(client=None, api_key=None, fallback_dimensions=4)
    chunks = [
        TextChunk(
            document_id="doc-1",
            chunk_id="chunk-1",
            chunk_index=0,
            page_number=2,
            text="source chunk",
            character_count=12,
        )
    ]

    embeddings = service.embed_chunks(chunks)

    assert len(embeddings) == 1
    assert embeddings[0].document_id == "doc-1"
    assert embeddings[0].chunk_id == "chunk-1"
    assert embeddings[0].chunk_index == 0
    assert embeddings[0].page_number == 2
    assert embeddings[0].text == "source chunk"
    assert embeddings[0].dimensions == 4


def test_provider_errors_fall_back_to_local_embeddings() -> None:
    service = EmbeddingService(client=FailingClient(), fallback_dimensions=5)

    embeddings = service.embed_texts(["still embedded"])

    assert len(embeddings) == 1
    assert embeddings[0].text == "still embedded"
    assert embeddings[0].dimensions == 5
    assert len(embeddings[0].embedding) == 5


def test_batch_size_must_be_positive() -> None:
    with pytest.raises(ValueError, match="batch_size must be greater than 0"):
        EmbeddingService(batch_size=0)
