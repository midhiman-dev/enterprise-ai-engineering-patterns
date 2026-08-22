"""Opt-in live integration smoke test for GroqRelevanceGrader against real Groq API.

This test requires a valid GROQ_API_KEY environment variable.
It is excluded from standard offline unit test runs via pytest marker config.
"""

import os
import pytest

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.generation.groq_client import GroqSdkChatClient
from corrective_rag.infrastructure.generation.groq_config import load_groq_config_from_env
from corrective_rag.infrastructure.grading.groq_relevance_grader import GroqRelevanceGrader


@pytest.mark.live
def test_groq_relevance_grader_live_smoke() -> None:
    """Smoke test verifying real Groq API call returns structurally valid GradedDocument."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        pytest.skip("GROQ_API_KEY environment variable is missing or empty.")

    config = load_groq_config_from_env()
    client = GroqSdkChatClient(api_key=config.api_key)
    grader = GroqRelevanceGrader(config=config, client=client)

    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    document = Document(
        content=(
            "CrashLoopBackOff indicates that a Kubernetes container repeatedly crashes "
            "shortly after starting. Common causes include exit code 1 due to application "
            "configuration errors, unhandled runtime exceptions, or failing liveness probes. "
            "Use kubectl logs to inspect container logs."
        ),
        source="k8s_troubleshooting_guide.md",
    )

    result = grader.grade(question=question, document=document)

    assert isinstance(result.is_relevant, bool)
    assert isinstance(result.reason, str)
    assert len(result.reason.strip()) > 0
    assert result.document == document
    assert result.score is None
