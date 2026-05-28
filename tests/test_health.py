from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_returns_project_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "GuardedRAG API",
        "version": "0.1.0",
    }


def test_health_returns_ok_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "guardedrag",
    }


def test_ready_returns_dependency_checks() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["service"] == "guardedrag"
    assert {check["name"] for check in body["checks"]} == {
        "configuration",
        "vector_store_path",
        "retrieval_settings",
        "chunking_settings",
    }
    assert all(check["available"] for check in body["checks"])


def test_openapi_uses_project_title() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "GuardedRAG API"


def test_openapi_documents_ready_endpoint() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/ready" in response.json()["paths"]
