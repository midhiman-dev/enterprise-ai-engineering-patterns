"""Unit tests for GroqRelevanceGrader infrastructure adapter using handwritten fake client."""

from collections.abc import Sequence

import pytest

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.generation.groq_config import GroqConfig
from corrective_rag.infrastructure.grading.groq_relevance_grader import (
    GroqRelevanceGrader,
    GroqRelevanceResult,
    parse_relevance_result,
)


class FakeGroqChatClient:
    """Handwritten in-memory fake Groq chat client for offline relevance grader unit testing."""

    def __init__(
        self,
        response_text: str = '{"is_relevant": true, "reason": "Default fake relevance response."}',
        exception_to_raise: Exception | None = None,
    ) -> None:
        self.response_text = response_text
        self.exception_to_raise = exception_to_raise

        self.last_model: str | None = None
        self.last_messages: Sequence[dict[str, str]] | None = None
        self.last_temperature: float | None = None
        self.call_count: int = 0

    def complete(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, str]],
        temperature: float,
    ) -> str:
        self.call_count += 1
        self.last_model = model
        self.last_messages = messages
        self.last_temperature = temperature

        if self.exception_to_raise is not None:
            raise self.exception_to_raise

        return self.response_text


@pytest.fixture
def dummy_config() -> GroqConfig:
    return GroqConfig(
        api_key="gsk_test_fake_key_12345",
        model="llama-3.3-70b-versatile",
        temperature=0.0,
    )


@pytest.fixture
def dummy_question() -> Question:
    return Question(text="Why does kubectl get pods show CrashLoopBackOff?")


@pytest.fixture
def relevant_document() -> Document:
    return Document(
        content="CrashLoopBackOff occurs when a container repeatedly starts, fails, and restarts.",
        source="k8s_troubleshooting.md",
    )


@pytest.fixture
def irrelevant_document() -> Document:
    return Document(
        content="ImagePullBackOff occurs when Kubernetes cannot pull the container image from the registry.",
        source="k8s_image_pull.md",
    )


def test_groq_relevance_grader_relevant_document(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 1: Grader maps structured relevant JSON response to Domain GradedDocument entity."""
    expected_reason = "Explains CrashLoopBackOff restart behavior."
    fake_json = f'{{"is_relevant": true, "reason": "{expected_reason}"}}'
    fake_client = FakeGroqChatClient(response_text=fake_json)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    result = grader.grade(question=dummy_question, document=relevant_document)

    assert result.document is relevant_document
    assert result.is_relevant is True
    assert result.reason == expected_reason
    assert result.score is None
    assert fake_client.call_count == 1
    assert fake_client.last_model == "llama-3.3-70b-versatile"
    assert fake_client.last_temperature == 0.0


def test_groq_relevance_grader_irrelevant_document(
    dummy_config: GroqConfig,
    dummy_question: Question,
    irrelevant_document: Document,
) -> None:
    """Test 2: Grader maps structured irrelevant JSON response (e.g. ImagePullBackOff vs CrashLoopBackOff)."""
    expected_reason = "Discusses image pulling rather than container restart failures."
    fake_json = f'{{"is_relevant": false, "reason": "{expected_reason}"}}'
    fake_client = FakeGroqChatClient(response_text=fake_json)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    result = grader.grade(question=dummy_question, document=irrelevant_document)

    assert result.document is irrelevant_document
    assert result.is_relevant is False
    assert result.reason == expected_reason
    assert result.score is None


def test_groq_relevance_grader_prompt_contains_question(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 3: Outgoing prompt contains exact original Question.text."""
    fake_client = FakeGroqChatClient()
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    grader.grade(question=dummy_question, document=relevant_document)

    assert fake_client.last_messages is not None
    user_message = next(
        msg["content"] for msg in fake_client.last_messages if msg["role"] == "user"
    )
    assert dummy_question.text in user_message


def test_groq_relevance_grader_prompt_contains_one_document(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 4: Outgoing prompt contains exactly the candidate document source and content."""
    fake_client = FakeGroqChatClient()
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    grader.grade(question=dummy_question, document=relevant_document)

    assert fake_client.last_messages is not None
    user_message = next(
        msg["content"] for msg in fake_client.last_messages if msg["role"] == "user"
    )
    assert "k8s_troubleshooting.md" in user_message
    assert "CrashLoopBackOff occurs when a container repeatedly starts" in user_message
    assert "k8s_image_pull.md" not in user_message


def test_groq_relevance_grader_json_boolean_type_validation(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 5: String "yes" for is_relevant fails type validation and raises RuntimeError."""
    fake_json = '{"is_relevant": "yes", "reason": "Looks relevant."}'
    fake_client = FakeGroqChatClient(response_text=fake_json)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    with pytest.raises(
        RuntimeError, match="Groq relevance grading returned invalid structured output."
    ):
        grader.grade(question=dummy_question, document=relevant_document)


def test_groq_relevance_grader_missing_field(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 6: Response missing required field 'reason' raises RuntimeError."""
    fake_json = '{"is_relevant": true}'
    fake_client = FakeGroqChatClient(response_text=fake_json)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    with pytest.raises(
        RuntimeError, match="Groq relevance grading returned invalid structured output."
    ):
        grader.grade(question=dummy_question, document=relevant_document)


def test_groq_relevance_grader_blank_reason(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 7: Response with blank whitespace 'reason' raises RuntimeError."""
    fake_json = '{"is_relevant": true, "reason": "   "}'
    fake_client = FakeGroqChatClient(response_text=fake_json)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    with pytest.raises(
        RuntimeError, match="Groq relevance grading returned invalid structured output."
    ):
        grader.grade(question=dummy_question, document=relevant_document)


def test_groq_relevance_grader_malformed_json(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 8: Plain text or malformed JSON raises RuntimeError with parse cause."""
    fake_text = "yes this document is relevant"
    fake_client = FakeGroqChatClient(response_text=fake_text)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    with pytest.raises(
        RuntimeError, match="Groq relevance grading returned invalid structured output."
    ) as exc_info:
        grader.grade(question=dummy_question, document=relevant_document)

    assert exc_info.value.__cause__ is not None


def test_groq_relevance_grader_blank_provider_output(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 9: Whitespace-only response raises RuntimeError."""
    fake_client = FakeGroqChatClient(response_text="   ")
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    with pytest.raises(
        RuntimeError, match="Groq relevance grading returned invalid structured output."
    ):
        grader.grade(question=dummy_question, document=relevant_document)


def test_groq_relevance_grader_preserves_provider_failure(
    dummy_config: GroqConfig,
    dummy_question: Question,
    relevant_document: Document,
) -> None:
    """Test 10: Provider API exceptions are preserved and NOT converted to is_relevant=False."""
    provider_error = RuntimeError("Groq API rate limit exceeded")
    fake_client = FakeGroqChatClient(exception_to_raise=provider_error)
    grader = GroqRelevanceGrader(config=dummy_config, client=fake_client)

    with pytest.raises(RuntimeError, match="Groq API rate limit exceeded"):
        grader.grade(question=dummy_question, document=relevant_document)


def test_parse_relevance_result_rejects_extra_unexpected_keys() -> None:
    """Parser unit test: Reject unexpected JSON keys to keep contract strict."""
    json_with_extra = '{"is_relevant": true, "reason": "Valid reason", "unexpected_score": 0.9}'

    with pytest.raises(
        RuntimeError, match="Groq relevance grading returned invalid structured output."
    ):
        parse_relevance_result(json_with_extra)


def test_parse_relevance_result_handles_markdown_code_fences() -> None:
    """Parser unit test: Unwraps standard JSON markdown code fences cleanly."""
    json_in_fences = '```json\n{"is_relevant": true, "reason": "Inside fence."}\n```'
    result = parse_relevance_result(json_in_fences)

    assert result.is_relevant is True
    assert result.reason == "Inside fence."
