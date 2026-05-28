from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.pdf_text_extractor import PDFExtractionError, PDFTextExtractor


SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    content_type: str
    character_count: int


DOCUMENT_METADATA_STORE: dict[str, DocumentMetadata] = {}


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

    text = _extract_text(content, extension)
    metadata = DocumentMetadata(
        document_id=str(uuid4()),
        filename=Path(filename).name,
        content_type=file.content_type or _default_content_type(extension),
        character_count=len(text),
    )
    DOCUMENT_METADATA_STORE[metadata.document_id] = metadata
    return metadata


def _extract_text(content: bytes, extension: str) -> str:
    if extension == ".txt":
        return content.decode("utf-8", errors="replace")
    try:
        result = PDFTextExtractor().extract(content)
    except PDFExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from PDF.",
        ) from exc
    return "\n".join(page.text for page in result.pages)


def _default_content_type(extension: str) -> str:
    if extension == ".pdf":
        return "application/pdf"
    return "text/plain"
