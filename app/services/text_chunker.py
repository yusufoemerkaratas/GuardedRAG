from __future__ import annotations

from hashlib import sha256

from pydantic import BaseModel, Field


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class TextPage(BaseModel):
    page_number: int | None = None
    text: str


class TextChunk(BaseModel):
    document_id: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    text: str
    character_count: int = Field(ge=0)


class RecursiveTextChunker:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, document_id: str, pages: list[TextPage]) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        for page in pages:
            page_chunks = self._split_text(page.text)
            for text in page_chunks:
                chunk_index = len(chunks)
                chunks.append(
                    TextChunk(
                        document_id=document_id,
                        chunk_id=self._stable_chunk_id(
                            document_id=document_id,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                            text=text,
                        ),
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        text=text,
                        character_count=len(text),
                    )
                )
        return chunks

    def chunk_text(
        self,
        document_id: str,
        text: str,
        page_number: int | None = None,
    ) -> list[TextChunk]:
        return self.chunk_pages(
            document_id=document_id,
            pages=[TextPage(page_number=page_number, text=text)],
        )

    def _split_text(self, text: str) -> list[str]:
        clean_text = text.strip()
        if not clean_text:
            return []
        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        chunks: list[str] = []
        start = 0
        while start < len(clean_text):
            end = min(start + self.chunk_size, len(clean_text))
            if end < len(clean_text):
                end = self._find_recursive_boundary(clean_text, start, end)

            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= len(clean_text):
                break

            start = max(end - self.chunk_overlap, 0)
            if start == end:
                start = end

        return chunks

    def _find_recursive_boundary(self, text: str, start: int, end: int) -> int:
        min_boundary = start + max(1, self.chunk_size // 2)
        for separator in ("\n\n", "\n", ". ", " ", ""):
            if not separator:
                return end

            boundary = text.rfind(separator, start, end)
            if boundary >= min_boundary:
                return boundary + len(separator)

        return end

    def _stable_chunk_id(
        self,
        document_id: str,
        page_number: int | None,
        chunk_index: int,
        text: str,
    ) -> str:
        raw_id = f"{document_id}:{page_number}:{chunk_index}:{text}"
        return sha256(raw_id.encode("utf-8")).hexdigest()
