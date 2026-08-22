"""Unit tests for document loader infrastructure."""

from pathlib import Path
import tempfile
import pytest

from corrective_rag.infrastructure.ingestion.document_loader import (
    SourceDocument,
    load_documents_from_directory,
)


def test_source_document_validation() -> None:
    doc = SourceDocument(
        content="Test content",
        source="test.md",
        metadata={"document_title": "Test Title"},
    )
    assert doc.content == "Test content"
    assert doc.source == "test.md"
    assert doc.metadata["document_title"] == "Test Title"

    with pytest.raises(ValueError, match="content cannot be empty"):
        SourceDocument(content="", source="test.md")

    with pytest.raises(ValueError, match="source cannot be empty"):
        SourceDocument(content="Content", source="   ")


def test_source_document_metadata_immutability() -> None:
    doc = SourceDocument(
        content="Test content",
        source="test.md",
        metadata={"key": "value"},
    )
    with pytest.raises(TypeError):
        doc.metadata["key"] = "new_value"  # type: ignore[index]


def test_load_documents_from_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create sample files
        f1 = tmp_path / "doc1.md"
        f1.write_text("# CrashLoop Troubleshooting\n\nPod keeps crashing.", encoding="utf-8")

        f2 = tmp_path / "doc2.txt"
        f2.write_text("Plain text document content.", encoding="utf-8")

        docs = load_documents_from_directory(tmp_path)
        assert len(docs) == 2

        # Sorted order: doc1.md, doc2.txt
        assert docs[0].source == "doc1.md"
        assert docs[0].metadata["document_title"] == "CrashLoop Troubleshooting"
        assert "Pod keeps crashing." in docs[0].content

        assert docs[1].source == "doc2.txt"
        assert docs[1].metadata["document_title"] == "doc2"
