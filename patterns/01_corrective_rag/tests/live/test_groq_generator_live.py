"""Opt-in live integration smoke test for GroqGenerator.

Must be explicitly selected using:
    pytest tests/live -m live -v

Requires a valid GROQ_API_KEY environment variable. Skips automatically if missing.
"""

import os

import pytest

from corrective_rag.domain.entities.answer import AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.generation.groq_client import GroqSdkChatClient
from corrective_rag.infrastructure.generation.groq_config import load_groq_config_from_env
from corrective_rag.infrastructure.generation.groq_generator import GroqGenerator


@pytest.mark.live
def test_groq_generator_live_smoke() -> None:
    """Live smoke test verifying Groq API connectivity and candidate generation.

    This test is excluded from normal deterministic CI runs.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        pytest.skip("GROQ_API_KEY environment variable is not configured.")

    config = load_groq_config_from_env()
    client = GroqSdkChatClient(api_key=config.api_key)
    generator = GroqGenerator(config=config, client=client)

    question = Question(text="Why can a Kubernetes pod enter CrashLoopBackOff status?")
    documents = [
        Document(
            content=(
                "A Kubernetes pod enters CrashLoopBackOff when one of its containers "
                "fails to start or exits repeatedly. Common causes include application "
                "runtime crashes (exit code 1 or 137), missing configuration/secrets, "
                "or failing readiness/liveness health checks."
            ),
            source="k8s_troubleshooting_guide.md",
        )
    ]

    answer = generator.generate(question=question, documents=documents)

    assert answer.status == AnswerStatus.ANSWERED
    assert answer.text is not None
    assert len(answer.text.strip()) > 0
