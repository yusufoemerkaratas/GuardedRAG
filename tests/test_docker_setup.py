from pathlib import Path


def test_dockerfile_runs_fastapi_on_port_8000() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "EXPOSE 8000" in dockerfile
    assert "uvicorn" in dockerfile
    assert "app.main:app" in dockerfile


def test_compose_exposes_api_and_mounts_app_volume() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert '"8000:8000"' in compose
    assert "./app:/app/app" in compose
    assert "--reload" in compose


def test_dockerignore_excludes_local_files() -> None:
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert ".git" in dockerignore
    assert ".venv" in dockerignore
    assert ".env" in dockerignore

