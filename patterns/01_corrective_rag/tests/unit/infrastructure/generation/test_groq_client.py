"""Unit tests for GroqSdkChatClient infrastructure adapter."""

from typing import Any

import pytest

from corrective_rag.infrastructure.generation.groq_client import GroqSdkChatClient


class FakeGroqInternalCompletions:
    """Tiny handwritten fake replacing the internal Groq SDK completions resource."""

    def __init__(self, response_choice_content: str = "Fake SDK response", exception_to_raise: Exception | None = None) -> None:
        self.response_choice_content = response_choice_content
        self.exception_to_raise = exception_to_raise

    def create(self, **kwargs: Any) -> Any:
        if self.exception_to_raise is not None:
            raise self.exception_to_raise

        class FakeChoiceMessage:
            def __init__(self, content: str) -> None:
                self.content = content

        class FakeChoice:
            def __init__(self, content: str) -> None:
                self.message = FakeChoiceMessage(content)

        class FakeResponse:
            def __init__(self, content: str) -> None:
                self.choices = [FakeChoice(content)]

        return FakeResponse(self.response_choice_content)


class FakeGroqInternalClient:
    """Tiny handwritten fake replacing the internal groq.Groq client instance."""

    def __init__(self, completions: FakeGroqInternalCompletions) -> None:
        class FakeChat:
            def __init__(self, completions_obj: FakeGroqInternalCompletions) -> None:
                self.completions = completions_obj

        self.chat = FakeChat(completions)


def test_groq_sdk_chat_client_success() -> None:
    """Tests GroqSdkChatClient extracts assistant content on success."""
    fake_completions = FakeGroqInternalCompletions(response_choice_content="Successfully generated answer.")
    client = GroqSdkChatClient(api_key="gsk_test_fake_key")
    client._client = FakeGroqInternalClient(fake_completions)  # type: ignore[assignment]

    result = client.complete(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.0,
    )

    assert result == "Successfully generated answer."


def test_groq_sdk_chat_client_safe_error_wrapping() -> None:
    """Tests GroqSdkChatClient wraps provider exceptions into safe RuntimeError and preserves cause."""
    raw_provider_error = ValueError("Sensitive connection error details with internal IP 10.0.0.1 and secret token")
    fake_completions = FakeGroqInternalCompletions(exception_to_raise=raw_provider_error)

    client = GroqSdkChatClient(api_key="gsk_test_fake_key")
    client._client = FakeGroqInternalClient(fake_completions)  # type: ignore[assignment]

    with pytest.raises(RuntimeError) as exc_info:
        client.complete(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.0,
        )

    # 1. Outer exception is RuntimeError
    assert exc_info.type is RuntimeError

    # 2. Outer message is exact static message
    assert str(exc_info.value) == "Groq API generation request failed."

    # 3. Exception cause is preserved
    assert exc_info.value.__cause__ is raw_provider_error

    # 4. Raw provider error details are excluded from outer message
    assert "Sensitive connection error details" not in str(exc_info.value)
    assert "10.0.0.1" not in str(exc_info.value)
