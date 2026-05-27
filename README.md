# GuardedRAG

GuardedRAG is a small source-grounded RAG API prototype. The project starts with
a minimal FastAPI backend and will grow issue by issue toward document upload,
chunking, retrieval, structured answers, citations, confidence scoring, and
fallback behavior when the provided context is not enough.

## Current Scope

Issue #1 provides the project foundation:

- FastAPI application package.
- Clean `app/api`, `app/core`, `app/schemas`, and `app/services` folders.
- Root endpoint with project metadata.
- `/health` endpoint.
- Pydantic response schema.
- Basic pytest coverage.
- Docker and Docker Compose setup.

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## Docker Setup

Optionally create a local environment file:

```bash
cp .env.example .env
```

Start the API:

```bash
docker compose up --build
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Tests

Run the test suite:

```bash
pytest
```

Quick import check:

```bash
python -c "from app.main import app; print(app.title)"
```

## API

### `GET /`

Returns project metadata.

Example response:

```json
{
  "name": "GuardedRAG API",
  "version": "0.1.0"
}
```

### `GET /health`

Returns a simple service status response.

Example response:

```json
{
  "status": "ok",
  "service": "guardedrag"
}
```
