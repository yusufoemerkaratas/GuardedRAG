from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(description="Stable ID assigned to the uploaded document.")
    filename: str
    content_type: str
    character_count: int
