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


def test_openapi_uses_project_title() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "GuardedRAG API"
