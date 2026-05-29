from app.schemas.documents import (
    ChunkMetadata,
    ChunkPreview,
    DocumentMetadata,
    DocumentUploadResponse,
)


def test_document_upload_response_serializes_metadata() -> None:
    response = DocumentUploadResponse(
        document_id="doc-1",
        filename="notes.txt",
        content_type="text/plain",
        character_count=42,
    )

    assert response.model_dump() == {
        "document_id": "doc-1",
        "filename": "notes.txt",
        "content_type": "text/plain",
        "character_count": 42,
    }


def test_upload_response_uses_document_metadata_contract() -> None:
    assert issubclass(DocumentUploadResponse, DocumentMetadata)


def test_chunk_metadata_serializes_identity_page_and_order() -> None:
    chunk = ChunkMetadata(
        document_id="doc-1",
        chunk_id="chunk-1",
        page_number=2,
        chunk_index=0,
        character_count=128,
    )

    assert chunk.model_dump() == {
        "document_id": "doc-1",
        "chunk_id": "chunk-1",
        "page_number": 2,
        "chunk_index": 0,
        "character_count": 128,
    }


def test_chunk_preview_includes_text_with_metadata() -> None:
    preview = ChunkPreview(
        document_id="doc-1",
        chunk_id="chunk-1",
        page_number=None,
        chunk_index=1,
        character_count=11,
        text="hello world",
    )

    assert preview.model_dump() == {
        "document_id": "doc-1",
        "chunk_id": "chunk-1",
        "page_number": None,
        "chunk_index": 1,
        "character_count": 11,
        "text": "hello world",
    }
