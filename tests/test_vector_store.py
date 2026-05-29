import asyncio

from app.services import document_ingestion
from app.services.document_ingestion import ingest_uploaded_document
from app.services.embeddings import ChunkEmbedding
from app.services.vector_store import SQLiteVectorStore


def _chunk_embedding(
    chunk_id: str = "chunk-1",
    document_id: str = "doc-1",
    chunk_index: int = 0,
) -> ChunkEmbedding:
    return ChunkEmbedding(
        document_id=document_id,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        page_number=3,
        text="stored chunk text",
        embedding=[0.1, 0.2, 0.3],
        dimensions=3,
    )


class FakeUploadFile:
    filename = "notes.txt"
    content_type = "text/plain"

    async def read(self) -> bytes:
        return b"GuardedRAG source text"


def test_vector_store_persists_chunk_embeddings(tmp_path) -> None:
    store = SQLiteVectorStore(tmp_path / "vector-store")
    store.upsert_chunks([_chunk_embedding()])

    reloaded_store = SQLiteVectorStore(tmp_path / "vector-store")
    vectors = reloaded_store.list_document_vectors("doc-1")

    assert len(vectors) == 1
    assert vectors[0].chunk_id == "chunk-1"
    assert vectors[0].document_id == "doc-1"
    assert vectors[0].chunk_index == 0
    assert vectors[0].page_number == 3
    assert vectors[0].text == "stored chunk text"
    assert vectors[0].embedding == [0.1, 0.2, 0.3]
    assert vectors[0].dimensions == 3


def test_vector_store_updates_existing_chunks(tmp_path) -> None:
    store = SQLiteVectorStore(tmp_path / "vector-store")
    store.upsert_chunks([_chunk_embedding()])
    store.upsert_chunks(
        [
            ChunkEmbedding(
                document_id="doc-1",
                chunk_id="chunk-1",
                chunk_index=0,
                page_number=None,
                text="updated",
                embedding=[0.9, 0.8],
                dimensions=2,
            )
        ]
    )

    vectors = store.list_document_vectors("doc-1")

    assert len(vectors) == 1
    assert vectors[0].text == "updated"
    assert vectors[0].embedding == [0.9, 0.8]
    assert vectors[0].dimensions == 2


def test_document_upload_ingestion_stores_embedded_chunks(tmp_path, monkeypatch) -> None:
    store = SQLiteVectorStore(tmp_path / "vector-store")
    monkeypatch.setattr(document_ingestion, "VECTOR_STORE", store)

    metadata = asyncio.run(ingest_uploaded_document(FakeUploadFile()))

    vectors = store.list_document_vectors(metadata.document_id)
    assert len(vectors) == 1
    assert vectors[0].document_id == metadata.document_id
    assert vectors[0].chunk_index == 0
    assert vectors[0].text == "GuardedRAG source text"
    assert vectors[0].dimensions > 0
