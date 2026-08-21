"""Unit tests for Answer domain entity."""

import pytest

from corrective_rag.domain.entities import Answer, AnswerStatus


def test_answer_successful_grounded_response() -> None:
    """Verifies creation of a grounded answer with default ANSWERED status."""
    text = "CrashLoopBackOff means the application in the container fails to start repeatedly."
    answer = Answer(text=text)

    assert answer.text == text
    assert answer.status == AnswerStatus.ANSWERED


def test_answer_unsupported_refusal_response() -> None:
    """Verifies creation of an explicit safe refusal answer with UNSUPPORTED status."""
    refusal_text = "I cannot support an answer for --enable-quantum-scheduler with available evidence."
    answer = Answer(text=refusal_text, status=AnswerStatus.UNSUPPORTED)

    assert answer.text == refusal_text
    assert answer.status == AnswerStatus.UNSUPPORTED


def test_answer_rejects_blank_text_for_all_statuses() -> None:
    """Verifies that empty or whitespace text is rejected for all AnswerStatus values."""
    with pytest.raises(ValueError, match="Answer text cannot be empty or whitespace-only"):
        Answer(text="", status=AnswerStatus.ANSWERED)

    with pytest.raises(ValueError, match="Answer text cannot be empty or whitespace-only"):
        Answer(text="   \n\t ", status=AnswerStatus.ANSWERED)

    with pytest.raises(ValueError, match="Answer text cannot be empty or whitespace-only"):
        Answer(text="", status=AnswerStatus.UNSUPPORTED)

    with pytest.raises(ValueError, match="Answer text cannot be empty or whitespace-only"):
        Answer(text="   \n\t ", status=AnswerStatus.UNSUPPORTED)
