"""Unit tests for Document domain entity."""

from datetime import date
import pytest

from corrective_rag.domain.entities import Document


def test_document_accepts_valid_content_and_source() -> None:
    """Verifies that a valid Document is created with mandatory fields."""
    content = "CrashLoopBackOff indicates a pod repeatedly starting and crashing."
    source = "k8s-docs/troubleshooting/pods.md"
    doc = Document(content=content, source=source)

    assert doc.content == content
    assert doc.source == source
    assert doc.title is None
    assert doc.source_url is None
    assert doc.snapshot_date is None
    assert doc.metadata == {}


def test_document_supports_optional_metadata_and_attributes() -> None:
    """Verifies that optional fields (title, url, date, metadata) are stored."""
    doc = Document(
        content="Pod eviction policies in Kubernetes 1.32...",
        source="tavily-web-search",
        title="Kubernetes 1.32 Release Notes",
        source_url="https://kubernetes.io/docs/concepts/scheduling-eviction/",
        snapshot_date=date(2026, 2, 1),
        metadata={"search_rank": 1, "provider": "tavily"},
    )

    assert doc.title == "Kubernetes 1.32 Release Notes"
    assert doc.source_url == "https://kubernetes.io/docs/concepts/scheduling-eviction/"
    assert doc.snapshot_date == date(2026, 2, 1)
    assert doc.metadata["search_rank"] == 1
    assert doc.metadata["provider"] == "tavily"


def test_document_rejects_empty_content() -> None:
    """Verifies that empty document content raises ValueError."""
    with pytest.raises(ValueError, match="Document content cannot be empty"):
        Document(content="", source="k8s-docs/pods.md")


def test_document_rejects_whitespace_content() -> None:
    """Verifies that whitespace-only document content raises ValueError."""
    with pytest.raises(ValueError, match="Document content cannot be empty"):
        Document(content="   \n  ", source="k8s-docs/pods.md")


def test_document_rejects_empty_source() -> None:
    """Verifies that empty document source raises ValueError."""
    with pytest.raises(ValueError, match="Document source cannot be empty"):
        Document(content="Valid content", source="")


def test_document_rejects_whitespace_source() -> None:
    """Verifies that whitespace-only document source raises ValueError."""
    with pytest.raises(ValueError, match="Document source cannot be empty"):
        Document(content="Valid content", source="   \t ")
