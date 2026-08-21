"""Unit tests for GradedDocument domain entity."""

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


def test_graded_document_preserves_numeric_score_without_range_restrictions() -> None:
    """Verifies that numeric score values are preserved without forcing a [0, 1] range contract."""
    doc = Document(content="Valid content", source="k8s-docs/pods.md")

    graded_high = GradedDocument(document=doc, is_relevant=True, score=7.4)
    assert graded_high.score == 7.4

    graded_raw = GradedDocument(document=doc, is_relevant=False, score=-12.5)
    assert graded_raw.score == -12.5
