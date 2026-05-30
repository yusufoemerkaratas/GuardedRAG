from app.schemas.retrieval import RetrievalSearchResult
from app.services.prompts import (
    CONTEXT_ONLY_SYSTEM_PROMPT,
    build_context_only_prompt,
)


def _context_chunk() -> RetrievalSearchResult:
    return RetrievalSearchResult(
        document_id="doc-1",
        chunk_id="chunk-1",
        chunk_index=0,
        page_number=4,
        text="Only this context may be used.",
        score=0.92,
    )


def test_context_only_prompt_contains_required_guardrails() -> None:
    prompt = CONTEXT_ONLY_SYSTEM_PROMPT

    assert "Use only the provided context" in prompt
    assert "Do not use general knowledge" in prompt
    assert "Do not make unsupported claims" in prompt
    assert "context is insufficient" in prompt
    assert "Always cite source chunks" in prompt
    assert "Return only valid JSON" in prompt


def test_context_only_prompt_includes_question_and_context() -> None:
    prompt = build_context_only_prompt(
        question="What does the source say?",
        context_chunks=[_context_chunk()],
    )

    assert "Question:" in prompt
    assert "What does the source say?" in prompt
    assert "Context:" in prompt
    assert "Only this context may be used." in prompt


def test_context_only_prompt_includes_source_metadata() -> None:
    prompt = build_context_only_prompt(
        question="What does the source say?",
        context_chunks=[_context_chunk()],
    )

    assert "chunk_id=chunk-1" in prompt
    assert "document_id=doc-1" in prompt
    assert "chunk_index=0" in prompt
    assert "page_number=4" in prompt
    assert "score=0.92" in prompt


def test_context_only_prompt_handles_empty_context() -> None:
    prompt = build_context_only_prompt(
        question="What does the source say?",
        context_chunks=[],
    )

    assert "No retrieved context was provided." in prompt
