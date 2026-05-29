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
- Document upload endpoint for TXT and PDF files.
- Page-level PDF text extraction service.
- Recursive text chunking with stable chunk metadata.
- Embedding service with local fallback for offline development and tests.
- Persistent local vector store for embedded document chunks.
- Retrieval and RAG query endpoints with source-aware responses.

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
http://127.0.0.1:8000/docs
```

Verify readiness:

```bash
curl http://127.0.0.1:8000/ready
```

Read container logs:

```bash
docker compose logs -f api
```

## Configuration

Configuration is read from environment variables. Local secrets should stay in
`.env`; never commit real API keys.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment label. |
| `APP_NAME` | `GuardedRAG API` | API title shown in OpenAPI. |
| `APP_VERSION` | `0.1.0` | API version shown in OpenAPI and root response. |
| `SERVICE_NAME` | `guardedrag` | Internal service name for health checks. |
| `OPENAI_API_KEY` | empty | Optional provider key for future model calls. |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name. |
| `CHAT_MODEL` | `gpt-4.1-mini` | Chat model name. |
| `VECTOR_STORE_PATH` | `data/vector_store` | Local vector store directory. |
| `TOP_K` | `5` | Number of retrieved chunks to return. |
| `SIMILARITY_THRESHOLD` | `0.75` | Minimum retrieval similarity score. |
| `CHUNK_SIZE` | `1000` | Target chunk size for document ingestion. |
| `CHUNK_OVERLAP` | `200` | Overlap between neighboring chunks. |

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

### `GET /ready`

Returns readiness status for core application dependencies and settings.

Example response:

```json
{
  "status": "ready",
  "service": "guardedrag",
  "checks": [
    {
      "name": "configuration",
      "available": true,
      "detail": "Application settings loaded."
    }
  ]
}
```

### `POST /documents/upload`

Uploads a TXT or PDF document for ingestion and returns basic metadata.
Unsupported file types and empty files return a clean `400` response.
PDF files are processed with a page-level extractor so later ingestion steps can
preserve page numbers for citations and retrieval context.

Example request:

```bash
curl -F "file=@notes.txt" http://127.0.0.1:8000/documents/upload
```

Example response:

```json
{
  "document_id": "5d58785b-79da-4ed8-a6f9-07ad2f02ec7f",
  "filename": "notes.txt",
  "content_type": "text/plain",
  "character_count": 42
}
```

### `POST /retrieval/search`

Embeds a query and returns the most relevant indexed chunks that pass the
configured similarity threshold. Empty vector stores or weak matches return an
empty result list with `answerable=false`.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What does the source say?", "top_k": 3}'
```

Example response:

```json
{
  "query": "What does the source say?",
  "results": [
    {
      "document_id": "5d58785b-79da-4ed8-a6f9-07ad2f02ec7f",
      "chunk_id": "4c912f5b6cb4d6717a4f7fcd3dd64d9cb389d0cf58d7a3bdb6e95da86b072e42",
      "chunk_index": 0,
      "page_number": null,
      "text": "GuardedRAG source text",
      "score": 0.91
    }
  ],
  "result_count": 1,
  "answerable": true,
  "similarity_threshold": 0.75
}
```

### `POST /rag/query`

Runs retrieval first, builds context only from chunks that pass the similarity
threshold, and returns a source-aware answer. If no context is strong enough,
the endpoint returns a fallback response without generating an answer.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the source say?", "top_k": 3}'
```

Example response:

```json
{
  "answer": "Based on the retrieved context: GuardedRAG source text",
  "answerable": true,
  "confidence": 0.91,
  "sources": [
    {
      "document_id": "5d58785b-79da-4ed8-a6f9-07ad2f02ec7f",
      "chunk_id": "4c912f5b6cb4d6717a4f7fcd3dd64d9cb389d0cf58d7a3bdb6e95da86b072e42",
      "chunk_index": 0,
      "page_number": null,
      "score": 0.91
    }
  ]
}
```
