import pytest

from app.services import pdf_text_extractor
from app.services.pdf_text_extractor import PDFExtractionError, PDFTextExtractor


class FakePage:
    def __init__(self, text: str | None) -> None:
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


class FakeReader:
    def __init__(self, content) -> None:
        self.pages = [
            FakePage("First page text"),
            FakePage(None),
            FakePage("Third page text"),
        ]


class FailingReader:
    def __init__(self, content) -> None:
        raise ValueError("broken pdf")


def test_pdf_text_extractor_returns_page_metadata(monkeypatch) -> None:
    monkeypatch.setattr(pdf_text_extractor, "PdfReader", FakeReader)

    result = PDFTextExtractor().extract(b"%PDF-1.4")

    assert result.page_count == 3
    assert result.character_count == 30
    assert [page.page_number for page in result.pages] == [1, 2, 3]
    assert [page.character_count for page in result.pages] == [15, 0, 15]
    assert result.pages[1].text == ""


def test_pdf_text_extractor_handles_sample_pdf_literal_text(monkeypatch) -> None:
    monkeypatch.setattr(pdf_text_extractor, "PdfReader", None)

    result = PDFTextExtractor().extract(
        b"%PDF-1.4\n1 0 obj <<>> stream\n(Sample PDF text)\nendstream\nendobj\n%%EOF"
    )

    assert result.page_count == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == "Sample PDF text"


def test_pdf_text_extractor_raises_clean_error_for_unreadable_pdf(monkeypatch) -> None:
    monkeypatch.setattr(pdf_text_extractor, "PdfReader", FailingReader)

    with pytest.raises(PDFExtractionError, match="Could not extract text from PDF"):
        PDFTextExtractor().extract(b"not a readable pdf")


def test_pdf_upload_returns_clean_error_when_extraction_fails(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(pdf_text_extractor, "PdfReader", FailingReader)
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        files={"file": ("broken.pdf", b"not a readable pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Could not extract text from PDF."}
