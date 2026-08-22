"""Unit tests for GroqQueryRewriter infrastructure adapter using handwritten fake client."""

from collections.abc import Sequence

import pytest

from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.generation.groq_config import GroqConfig
from corrective_rag.infrastructure.search.groq_query_rewriter import GroqQueryRewriter


class FakeGroqChatClient:
    """Handwritten in-memory fake Groq chat client for offline unit testing."""

    def __init__(
        self,
        response_text: str = "Default fake search query.",
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


def test_groq_query_rewriter_successful_rewrite(dummy_config: GroqConfig) -> None:
    """Test 1: GroqQueryRewriter maps successful provider response to Domain Question entity."""
    original = Question(
        "How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?"
    )
    expected_query = (
        "Kubernetes 1.32 node-pressure eviction policy pod eviction documentation"
    )
    fake_client = FakeGroqChatClient(response_text=expected_query)
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    result = rewriter.rewrite(original)

    assert isinstance(result, Question)
    assert result.text == expected_query
    assert fake_client.call_count == 1


def test_groq_query_rewriter_original_question_sent_to_prompt(
    dummy_config: GroqConfig,
) -> None:
    """Test 2: Original question text appears in the outgoing user message."""
    question_text = (
        "How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?"
    )
    original = Question(question_text)
    fake_client = FakeGroqChatClient()
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    rewriter.rewrite(original)

    assert fake_client.last_messages is not None
    user_msg = next(
        msg["content"] for msg in fake_client.last_messages if msg["role"] == "user"
    )
    assert question_text in user_msg


def test_groq_query_rewriter_prompt_says_do_not_answer(
    dummy_config: GroqConfig,
) -> None:
    """Test 3: Prompt instructions state rewrite for search and do not answer."""
    original = Question("Why does pod enter CrashLoopBackOff?")
    fake_client = FakeGroqChatClient()
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    rewriter.rewrite(original)

    assert fake_client.last_messages is not None
    system_msg = next(
        msg["content"] for msg in fake_client.last_messages if msg["role"] == "system"
    )
    assert "rewrite" in system_msg.lower()
    assert "Do NOT attempt to answer" in system_msg


def test_groq_query_rewriter_preserves_technical_identifiers(
    dummy_config: GroqConfig,
) -> None:
    """Test 4: Technical identifiers and versions reach the outgoing messages unchanged."""
    version_str = "Kubernetes 1.32"
    original = Question(
        f"How do I handle pod eviction under {version_str}'s new node-pressure eviction policy?"
    )
    fake_client = FakeGroqChatClient()
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    rewriter.rewrite(original)

    assert fake_client.last_messages is not None
    user_msg = next(
        msg["content"] for msg in fake_client.last_messages if msg["role"] == "user"
    )
    assert version_str in user_msg


def test_groq_query_rewriter_fabricated_premise_query(
    dummy_config: GroqConfig,
) -> None:
    """Test 5: Fabricated-premise query returns search query without answering."""
    fictional_question = Question(
        "What does the --enable-quantum-scheduler flag do in kubectl?"
    )
    expected_search_query = "kubectl --enable-quantum-scheduler flag documentation"
    fake_client = FakeGroqChatClient(response_text=expected_search_query)
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    result = rewriter.rewrite(fictional_question)

    assert isinstance(result, Question)
    assert result.text == expected_search_query
    # Verify adapter did not raise or mutate state
    assert fake_client.call_count == 1


def test_groq_query_rewriter_rejects_blank_provider_response(
    dummy_config: GroqConfig,
) -> None:
    """Test 6: Rewriter raises RuntimeError on empty provider response."""
    original = Question("How do I fix CrashLoopBackOff?")
    fake_client = FakeGroqChatClient(response_text="")
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    with pytest.raises(RuntimeError, match="Groq returned an empty rewritten query."):
        rewriter.rewrite(original)


def test_groq_query_rewriter_rejects_whitespace_provider_response(
    dummy_config: GroqConfig,
) -> None:
    """Test 7: Rewriter raises RuntimeError on whitespace-only provider response."""
    original = Question("How do I fix CrashLoopBackOff?")
    fake_client = FakeGroqChatClient(response_text="   \n ")
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    with pytest.raises(RuntimeError, match="Groq returned an empty rewritten query."):
        rewriter.rewrite(original)


def test_groq_query_rewriter_trims_whitespace_around_valid_query(
    dummy_config: GroqConfig,
) -> None:
    """Test 8: Rewriter trims leading and trailing whitespace from provider response."""
    original = Question("How do I fix CrashLoopBackOff?")
    raw_response = "  Kubernetes pod eviction documentation  "
    fake_client = FakeGroqChatClient(response_text=raw_response)
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    result = rewriter.rewrite(original)

    assert result.text == "Kubernetes pod eviction documentation"


def test_groq_query_rewriter_preserves_provider_failure(
    dummy_config: GroqConfig,
) -> None:
    """Test 9: Provider failure propagates as operational failure, not silent fallback."""
    original = Question("How do I fix CrashLoopBackOff?")
    provider_error = RuntimeError("Groq API rate limit exceeded")
    fake_client = FakeGroqChatClient(exception_to_raise=provider_error)
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    with pytest.raises(RuntimeError, match="Groq API rate limit exceeded"):
        rewriter.rewrite(original)


def test_groq_query_rewriter_forwards_config(dummy_config: GroqConfig) -> None:
    """Test 10: Rewriter passes model and temperature parameters from GroqConfig."""
    original = Question("How do I fix CrashLoopBackOff?")
    fake_client = FakeGroqChatClient()
    rewriter = GroqQueryRewriter(config=dummy_config, client=fake_client)

    rewriter.rewrite(original)

    assert fake_client.last_model == "llama-3.3-70b-versatile"
    assert fake_client.last_temperature == 0.0
