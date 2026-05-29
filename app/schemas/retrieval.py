from pydantic import BaseModel, Field


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1)


class RetrievalSearchResult(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    text: str
    score: float


class RetrievalSearchResponse(BaseModel):
    query: str
    results: list[RetrievalSearchResult]
    result_count: int = Field(ge=0)
