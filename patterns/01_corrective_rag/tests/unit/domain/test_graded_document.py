"""Unit tests for GradedDocument domain entity."""

import pytest

from corrective_rag.domain.entities import Document, GradedDocument


def test_graded_document_relevant_without_score() -> None:
    """Verifies creation of a relevant graded document with essential boolean decision."""
    doc = Document(content="Pod crash details...", source="k8s-docs/pods.md")
    graded = GradedDocument(document=doc, is_relevant=True)

    assert graded.document == doc
    assert graded.is_relevant is True
    assert graded.score is None
    assert graded.reason is None


def test_graded_document_irrelevant_with_score_and_reason() -> None:
    """Verifies creation of an irrelevant graded document with score and reason."""
    doc = Document(content="Unrelated network policy details...", source="k8s-docs/net.md")
    graded = GradedDocument(
        document=doc,
        is_relevant=False,
        score=0.15,
        reason="Document describes network policies rather than pod lifecycle status.",
    )

    assert graded.document == doc
    assert graded.is_relevant is False
    assert graded.score == 0.15
    assert graded.reason == "Document describes network policies rather than pod lifecycle status."


def test_graded_document_rejects_score_out_of_range() -> None:
    """Verifies that numeric score outside 0.0 to 1.0 raises ValueError."""
    doc = Document(content="Valid content", source="k8s-docs/pods.md")

    with pytest.raises(ValueError, match="score must be between 0.0 and 1.0"):
        GradedDocument(document=doc, is_relevant=True, score=1.5)

    with pytest.raises(ValueError, match="score must be between 0.0 and 1.0"):
        GradedDocument(document=doc, is_relevant=False, score=-0.1)
