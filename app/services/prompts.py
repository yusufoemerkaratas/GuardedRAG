from __future__ import annotations

from app.schemas.retrieval import RetrievalSearchResult


CONTEXT_ONLY_SYSTEM_PROMPT = """You are GuardedRAG, a source-grounded assistant.

Rules:
- Use only the provided context.
- Do not use general knowledge.
- Do not make unsupported claims.
- If the context is insufficient, set answerable to false and explain that the indexed sources do not contain enough information.
- Always cite source chunks in the sources array.
- Return only valid JSON matching this shape:
  {
    "answer": "string",
    "answerable": true,
    "confidence": 0.0,
    "sources": [
      {
        "document_id": "string",
        "chunk_id": "string",
        "chunk_index": 0,
        "page_number": null,
        "score": 0.0
      }
    ]
  }
"""


def build_context_only_prompt(
    question: str,
    context_chunks: list[RetrievalSearchResult],
) -> str:
    context = "\n\n".join(
        _format_context_chunk(chunk)
        for chunk in context_chunks
    )
    return (
        f"{CONTEXT_ONLY_SYSTEM_PROMPT}\n"
        "Question:\n"
        f"{question}\n\n"
        "Context:\n"
        f"{context if context else 'No retrieved context was provided.'}"
    )


def _format_context_chunk(chunk: RetrievalSearchResult) -> str:
    page = "unknown" if chunk.page_number is None else str(chunk.page_number)
    return (
        f"[source chunk_id={chunk.chunk_id} document_id={chunk.document_id} "
        f"chunk_index={chunk.chunk_index} page_number={page} score={chunk.score}]\n"
        f"{chunk.text}"
    )
