from __future__ import annotations

import re
from io import BytesIO

from pydantic import BaseModel

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency is declared for runtime
    PdfReader = None


class PDFExtractionError(Exception):
    """Raised when PDF text extraction cannot read the uploaded document."""


class PDFPageText(BaseModel):
    page_number: int
    text: str
    character_count: int


class PDFTextExtractionResult(BaseModel):
    pages: list[PDFPageText]
    page_count: int
    character_count: int


class PDFTextExtractor:
    def extract(self, content: bytes) -> PDFTextExtractionResult:
        if not content:
            raise PDFExtractionError("PDF content is empty.")

        if PdfReader is not None:
            try:
                return self._extract_with_pypdf(content)
            except Exception as exc:
                fallback = self._extract_literal_text(content)
                if fallback.pages:
                    return fallback
                raise PDFExtractionError("Could not extract text from PDF.") from exc

        fallback = self._extract_literal_text(content)
        if fallback.pages:
            return fallback
        raise PDFExtractionError("Could not extract text from PDF.")

    def _extract_with_pypdf(self, content: bytes) -> PDFTextExtractionResult:
        reader = PdfReader(BytesIO(content))
        pages = [
            self._build_page_text(page_number=index, text=page.extract_text() or "")
            for index, page in enumerate(reader.pages, start=1)
        ]
        return self._build_result(pages)

    def _extract_literal_text(self, content: bytes) -> PDFTextExtractionResult:
        decoded = content.decode("latin-1", errors="ignore")
        values = re.findall(r"\((.*?)\)", decoded, re.DOTALL)
        pages = [
            self._build_page_text(page_number=index, text=_decode_pdf_literal(value))
            for index, value in enumerate(values, start=1)
        ]
        return self._build_result(pages)

    def _build_page_text(self, page_number: int, text: str) -> PDFPageText:
        return PDFPageText(
            page_number=page_number,
            text=text,
            character_count=len(text),
        )

    def _build_result(self, pages: list[PDFPageText]) -> PDFTextExtractionResult:
        return PDFTextExtractionResult(
            pages=pages,
            page_count=len(pages),
            character_count=sum(page.character_count for page in pages),
        )


def _decode_pdf_literal(value: str) -> str:
    return value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
