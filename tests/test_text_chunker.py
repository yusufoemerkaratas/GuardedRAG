import pytest

from app.services.text_chunker import RecursiveTextChunker, TextPage


def test_long_document_is_split_into_ordered_chunks() -> None:
    chunker = RecursiveTextChunker(chunk_size=10, chunk_overlap=2)

    chunks = chunker.chunk_text(document_id="doc-1", text="abcdefghijklmnopqrstuv")

    assert [chunk.text for chunk in chunks] == ["abcdefghij", "ijklmnopqr", "qrstuv"]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert all(chunk.document_id == "doc-1" for chunk in chunks)
    assert all(chunk.character_count <= 10 for chunk in chunks)


def test_chunk_overlap_preserves_trailing_context() -> None:
    chunker = RecursiveTextChunker(chunk_size=10, chunk_overlap=3)

    chunks = chunker.chunk_text(document_id="doc-1", text="abcdefghijklmnopqrstuvwxyz")

    assert chunks[0].text[-3:] == chunks[1].text[:3]
    assert chunks[1].text[-3:] == chunks[2].text[:3]


def test_chunks_preserve_page_number_metadata() -> None:
    chunker = RecursiveTextChunker(chunk_size=8, chunk_overlap=2)

    chunks = chunker.chunk_pages(
        document_id="doc-2",
        pages=[
            TextPage(page_number=1, text="alpha beta"),
            TextPage(page_number=2, text="gamma delta"),
        ],
    )

    assert [chunk.page_number for chunk in chunks] == [1, 1, 2, 2]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3]


def test_chunk_ids_are_stable_for_same_input() -> None:
    chunker = RecursiveTextChunker(chunk_size=12, chunk_overlap=4)

    first_run = chunker.chunk_text(document_id="stable-doc", text="same text repeated same text")
    second_run = chunker.chunk_text(document_id="stable-doc", text="same text repeated same text")

    assert [chunk.chunk_id for chunk in first_run] == [chunk.chunk_id for chunk in second_run]


def test_recursive_chunker_prefers_sentence_boundary() -> None:
    chunker = RecursiveTextChunker(chunk_size=28, chunk_overlap=5)

    chunks = chunker.chunk_text(
        document_id="doc-3",
        text="First sentence. Second sentence continues.",
    )

    assert chunks[0].text == "First sentence."


def test_empty_text_returns_no_chunks() -> None:
    chunker = RecursiveTextChunker()

    assert chunker.chunk_text(document_id="doc-empty", text="   ") == []


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be smaller"):
        RecursiveTextChunker(chunk_size=100, chunk_overlap=100)
