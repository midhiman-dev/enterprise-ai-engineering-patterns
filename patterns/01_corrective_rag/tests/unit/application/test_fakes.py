"""Unit tests for handwritten deterministic test fakes validation and sequence handling."""

import pytest

from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from tests.unit.application.fakes import FakeGenerator, FakeHallucinationChecker


def test_fake_generator_rejects_empty_answer_sequence() -> None:
    """Verifies that FakeGenerator raises ValueError when passed an empty answers sequence."""
    with pytest.raises(ValueError, match="answers must contain at least one Answer"):
        FakeGenerator(answers=[])


def test_fake_hallucination_checker_rejects_empty_result_sequence() -> None:
    """Verifies that FakeHallucinationChecker raises ValueError when passed an empty results sequence."""
    with pytest.raises(ValueError, match="results must contain at least one boolean result"):
        FakeHallucinationChecker(results=[])


def test_fake_generator_sequence_and_fallback_behavior() -> None:
    """Verifies that FakeGenerator returns answers sequentially and repeats the last answer on overflow."""
    q = Question(text="Test question?")
    docs = [Document(content="doc content", source="source")]
    ans1 = Answer(text="Answer 1", status=AnswerStatus.ANSWERED)
    ans2 = Answer(text="Answer 2", status=AnswerStatus.ANSWERED)

    fake_gen = FakeGenerator(answers=[ans1, ans2])
    assert fake_gen.generate(q, docs) == ans1
    assert fake_gen.generate(q, docs) == ans2
    assert fake_gen.generate(q, docs) == ans2  # Overflow uses last element


def test_fake_hallucination_checker_sequence_and_fallback_behavior() -> None:
    """Verifies that FakeHallucinationChecker returns results sequentially and repeats the last result on overflow."""
    ans = Answer(text="Answer text", status=AnswerStatus.ANSWERED)
    docs = [Document(content="doc content", source="source")]

    fake_checker = FakeHallucinationChecker(results=[False, True])
    assert fake_checker.is_supported(ans, docs) is False
    assert fake_checker.is_supported(ans, docs) is True
    assert fake_checker.is_supported(ans, docs) is True  # Overflow uses last element
