"""Unit tests for Question domain entity."""

import pytest

from corrective_rag.domain.entities import Question


def test_question_accepts_valid_text() -> None:
    """Verifies that a valid question is instantiated with preserved text."""
    text = "Why does kubectl get pods show CrashLoopBackOff?"
    question = Question(text=text)

    assert question.text == text


def test_question_preserves_exact_user_wording() -> None:
    """Verifies that user question text is preserved exactly without rewriting."""
    exact_wording = "  How do I troubleshoot Pod Eviction in K8s 1.32?  "
    question = Question(text=exact_wording)

    assert question.text == exact_wording


def test_question_rejects_empty_text() -> None:
    """Verifies that empty question text raises ValueError."""
    with pytest.raises(ValueError, match="Question text cannot be empty"):
        Question(text="")


def test_question_rejects_whitespace_only_text() -> None:
    """Verifies that whitespace-only question text raises ValueError."""
    with pytest.raises(ValueError, match="Question text cannot be empty"):
        Question(text="   \n\t  ")
