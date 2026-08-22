"""Unit tests for document chunker infrastructure."""

import pytest

from corrective_rag.infrastructure.ingestion.chunker import (
    DocumentChunk,
    DocumentChunker,
)
from corrective_rag.infrastructure.ingestion.document_loader import SourceDocument


def test_chunker_invariant_validations() -> None:
    with pytest.raises(ValueError, match="chunk_size must be > 0"):
        DocumentChunker(chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError, match="chunk_overlap must be >= 0"):
        DocumentChunker(chunk_size=100, chunk_overlap=-5)

    with pytest.raises(ValueError, match="must be strictly less than chunk_size"):
        DocumentChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="must be strictly less than chunk_size"):
        DocumentChunker(chunk_size=100, chunk_overlap=120)


def test_short_document_single_chunk() -> None:
    doc = SourceDocument(
        content="Short document text fits in single chunk.",
        source="short.md",
        metadata={"document_title": "Short Doc"},
    )
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "short.md::chunk_0"
    assert chunks[0].content == "Short document text fits in single chunk."
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata["source"] == "short.md"
    assert chunks[0].metadata["document_title"] == "Short Doc"


def test_long_document_multiple_chunks_and_overlap() -> None:
    content = "Paragraph 1: " + "A" * 80 + "\n\nParagraph 2: " + "B" * 80 + "\n\nParagraph 3: " + "C" * 80
    doc = SourceDocument(content=content, source="long.md")

    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= 100

    # Test chunk index increment and chunk IDs
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_index == idx
        assert chunk.chunk_id == f"long.md::chunk_{idx}"


def test_blank_or_empty_document() -> None:
    with pytest.raises(ValueError, match="content cannot be empty"):
        SourceDocument(content="   ", source="empty.md")


def test_deterministic_chunk_ids() -> None:
    doc1 = SourceDocument(content="Some document content for deterministic test.", source="k8s.md")
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)

    chunks1 = chunker.chunk_document(doc1)
    chunks2 = chunker.chunk_document(doc1)

    assert [c.chunk_id for c in chunks1] == [c.chunk_id for c in chunks2]
    assert chunks1[0].chunk_id == "k8s.md::chunk_0"
