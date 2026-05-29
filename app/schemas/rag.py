from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1)


class RAGSource(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    score: float


class RAGQueryResponse(BaseModel):
    answer: str
    answerable: bool
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[RAGSource]
