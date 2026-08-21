"""Unit tests for Question domain entity."""

from datetime import datetime
import pytest

from corrective_rag.domain.entities import Question


def test_question_accepts_valid_text() -> None:
    """Verifies that a valid question is instantiated with preserved text."""
    text = "Why does kubectl get pods show CrashLoopBackOff?"
    question = Question(text=text)

    assert question.text == text
    assert isinstance(question.id, str)
    assert len(question.id) > 0
    assert isinstance(question.created_at, datetime)


def test_question_preserves_exact_user_wording() -> None:
    """Verifies that user question text is preserved exactly without rewriting."""
    exact_wording = "  How do I troubleshoot Pod Eviction in K8s 1.32?  "
    # Leading/trailing whitespace in string content is preserved unless explicitly blank
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


def test_question_supports_custom_id_and_timestamp() -> None:
    """Verifies that custom ID and creation timestamp can be supplied."""
    custom_id = "q-12345"
    custom_time = datetime(2026, 1, 1, 12, 0, 0)
    question = Question(text="What is pod eviction?", id=custom_id, created_at=custom_time)

    assert question.id == custom_id
    assert question.created_at == custom_time
