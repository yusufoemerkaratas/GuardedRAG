from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str = Field(description="Stable ID assigned to the uploaded document.")
    filename: str
    content_type: str
    character_count: int


class DocumentUploadResponse(DocumentMetadata):
    pass


class ChunkMetadata(BaseModel):
    document_id: str
    chunk_id: str
    page_number: int | None = None
    chunk_index: int = Field(ge=0)
    character_count: int = Field(ge=0)


class ChunkPreview(ChunkMetadata):
    text: str
