"""Unit tests for GroqGenerator infrastructure adapter using handwritten fake client."""

from collections.abc import Sequence
from typing import Any

import pytest

from corrective_rag.domain.entities.answer import AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.generation.groq_config import GroqConfig
from corrective_rag.infrastructure.generation.groq_generator import GroqGenerator


class FakeGroqChatClient:
    """Handwritten in-memory fake Groq chat client for offline unit testing."""

    def __init__(
        self,
        response_text: str = "Default fake LLM response text.",
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
def dummy_documents() -> list[Document]:
    return [
        Document(
            content="CrashLoopBackOff indicates a container repeatedly fails after starting. Check container logs with kubectl logs.",
            source="k8s_troubleshooting.md",
        ),
        Document(
            content="Common causes include exit code 1, missing environment variables, or failing liveness probes.",
            source="k8s_pod_lifecycle.md",
        ),
    ]


def test_groq_generator_maps_response_to_domain_answer(
    dummy_config: GroqConfig,
    dummy_question: Question,
    dummy_documents: list[Document],
) -> None:
    """Test 1: GroqGenerator maps successful provider response to Domain Answer entity."""
    expected_text = (
        "Inspect container logs using kubectl logs and check liveness probes."
    )
    fake_client = FakeGroqChatClient(response_text=expected_text)
    generator = GroqGenerator(config=dummy_config, client=fake_client)

    answer = generator.generate(question=dummy_question, documents=dummy_documents)

    assert answer.status == AnswerStatus.ANSWERED
    assert answer.text == expected_text
    assert fake_client.call_count == 1
    assert fake_client.last_model == "llama-3.3-70b-versatile"
    assert fake_client.last_temperature == 0.0


def test_groq_generator_prompt_contains_original_question(
    dummy_config: GroqConfig,
    dummy_question: Question,
    dummy_documents: list[Document],
) -> None:
    """Test 2 & Test 4: Outgoing prompt contains exact original Question text."""
    fake_client = FakeGroqChatClient()
    generator = GroqGenerator(config=dummy_config, client=fake_client)

    generator.generate(question=dummy_question, documents=dummy_documents)

    assert fake_client.last_messages is not None
    user_message = next(
        msg["content"]
        for msg in fake_client.last_messages
        if msg["role"] == "user"
    )
    assert dummy_question.text in user_message


def test_groq_generator_prompt_contains_evidence_sources_and_contents(
    dummy_config: GroqConfig,
    dummy_question: Question,
    dummy_documents: list[Document],
) -> None:
    """Test 3: Outgoing prompt contains evidence source identifiers and document content."""
    fake_client = FakeGroqChatClient()
    generator = GroqGenerator(config=dummy_config, client=fake_client)

    generator.generate(question=dummy_question, documents=dummy_documents)

    assert fake_client.last_messages is not None
    user_message = next(
        msg["content"]
        for msg in fake_client.last_messages
        if msg["role"] == "user"
    )
    assert "k8s_troubleshooting.md" in user_message
    assert "CrashLoopBackOff indicates a container repeatedly fails" in user_message
    assert "k8s_pod_lifecycle.md" in user_message
    assert "failing liveness probes" in user_message


def test_groq_generator_rejects_empty_documents(
    dummy_config: GroqConfig,
    dummy_question: Question,
) -> None:
    """Test 5: Generator raises ValueError if evidence documents list is empty."""
    fake_client = FakeGroqChatClient()
    generator = GroqGenerator(config=dummy_config, client=fake_client)

    with pytest.raises(
        ValueError, match="GroqGenerator requires at least one evidence document."
    ):
        generator.generate(question=dummy_question, documents=[])

    assert fake_client.call_count == 0


def test_groq_generator_rejects_blank_provider_response(
    dummy_config: GroqConfig,
    dummy_question: Question,
    dummy_documents: list[Document],
) -> None:
    """Test 6: Generator raises RuntimeError if provider returns empty/whitespace content."""
    fake_client = FakeGroqChatClient(response_text="   ")
    generator = GroqGenerator(config=dummy_config, client=fake_client)

    with pytest.raises(
        RuntimeError, match="Groq returned an empty generation response."
    ):
        generator.generate(question=dummy_question, documents=dummy_documents)


def test_groq_generator_preserves_provider_failure(
    dummy_config: GroqConfig,
    dummy_question: Question,
    dummy_documents: list[Document],
) -> None:
    """Test 7: Generator preserves provider exceptions rather than returning AnswerStatus.UNSUPPORTED."""
    provider_error = RuntimeError("Groq API rate limit exceeded")
    fake_client = FakeGroqChatClient(exception_to_raise=provider_error)
    generator = GroqGenerator(config=dummy_config, client=fake_client)

    with pytest.raises(RuntimeError, match="Groq API rate limit exceeded"):
        generator.generate(question=dummy_question, documents=dummy_documents)
