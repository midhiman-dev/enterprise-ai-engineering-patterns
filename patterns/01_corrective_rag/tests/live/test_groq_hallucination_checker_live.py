"""Opt-in live integration smoke test for GroqHallucinationChecker against real Groq API.

This test requires a valid GROQ_API_KEY environment variable.
It is excluded from standard offline unit test runs via pytest marker config.
"""

import os
import pytest

from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.infrastructure.generation.groq_client import GroqSdkChatClient
from corrective_rag.infrastructure.generation.groq_config import load_groq_config_from_env
from corrective_rag.infrastructure.verification.groq_hallucination_checker import (
    GroqHallucinationChecker,
)


@pytest.mark.live
def test_groq_hallucination_checker_live_smoke() -> None:
    """Smoke test verifying real Groq API call returns boolean grounding support result."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        pytest.skip("GROQ_API_KEY environment variable is missing or empty.")

    config = load_groq_config_from_env()
    client = GroqSdkChatClient(api_key=config.api_key)
    checker = GroqHallucinationChecker(config=config, client=client)

    document = Document(
        content=(
            "A Kubernetes Pod can enter CrashLoopBackOff when a container repeatedly starts and exits "
            "due to application configuration errors, missing environment variables, or runtime crashes."
        ),
        source="k8s_troubleshooting_guide.md",
    )
    answer = Answer(
        text="CrashLoopBackOff can occur when a container repeatedly starts and exits due to runtime crashes or configuration errors.",
        status=AnswerStatus.ANSWERED,
    )

    result = checker.is_supported(answer=answer, documents=[document])

    assert isinstance(result, bool)
    assert result is True
