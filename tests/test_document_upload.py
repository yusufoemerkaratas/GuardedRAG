from fastapi.testclient import TestClient

from app.main import app
from app.services.document_ingestion import DOCUMENT_METADATA_STORE


client = TestClient(app)


def test_txt_upload_returns_document_metadata() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"GuardedRAG source text", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"]
    assert body["filename"] == "notes.txt"
    assert body["content_type"] == "text/plain"
    assert body["character_count"] == 22
    assert body["document_id"] in DOCUMENT_METADATA_STORE


def test_pdf_upload_returns_document_metadata() -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "source.pdf",
                b"%PDF-1.4\n1 0 obj <<>> stream\n(GuardedRAG PDF text)\nendstream\nendobj\n%%EOF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"]
    assert body["filename"] == "source.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["character_count"] > 0


def test_unsupported_file_type_returns_clean_error() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("image.png", b"not supported", "image/png")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Unsupported file type. Upload a TXT or PDF file.",
    }


def test_empty_file_is_rejected() -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


def test_openapi_documents_upload_endpoint() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/documents/upload" in response.json()["paths"]
