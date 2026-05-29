from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.documents import DocumentMetadata
from app.services.embeddings import EmbeddingService
from app.services.pdf_text_extractor import PDFExtractionError, PDFTextExtractor
from app.services.text_chunker import RecursiveTextChunker, TextPage
from app.services.vector_store import SQLiteVectorStore


SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


DOCUMENT_METADATA_STORE: dict[str, DocumentMetadata] = {}
VECTOR_STORE = SQLiteVectorStore(settings.vector_store_path)


async def ingest_uploaded_document(file: UploadFile) -> DocumentMetadata:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a TXT or PDF file.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    pages = _extract_pages(content, extension)
    text = "\n".join(page.text for page in pages)
    metadata = DocumentMetadata(
        document_id=str(uuid4()),
        filename=Path(filename).name,
        content_type=file.content_type or _default_content_type(extension),
        character_count=len(text),
    )
    chunks = RecursiveTextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    ).chunk_pages(document_id=metadata.document_id, pages=pages)
    chunk_embeddings = EmbeddingService().embed_chunks(chunks)
    VECTOR_STORE.upsert_chunks(chunk_embeddings)
    DOCUMENT_METADATA_STORE[metadata.document_id] = metadata
    return metadata


def _extract_pages(content: bytes, extension: str) -> list[TextPage]:
    if extension == ".txt":
        return [TextPage(text=content.decode("utf-8", errors="replace"))]
    try:
        result = PDFTextExtractor().extract(content)
    except PDFExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from PDF.",
        ) from exc
    return [
        TextPage(page_number=page.page_number, text=page.text)
        for page in result.pages
    ]


def _default_content_type(extension: str) -> str:
    if extension == ".pdf":
        return "application/pdf"
    return "text/plain"
