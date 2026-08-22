"""Opt-in live integration smoke test for GroqQueryRewriter.

Must be explicitly selected using:
    pytest tests/live -m live -v

Requires a valid GROQ_API_KEY environment variable. Skips automatically if missing.
"""

import os

import pytest

from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.generation.groq_client import GroqSdkChatClient
from corrective_rag.infrastructure.generation.groq_config import load_groq_config_from_env
from corrective_rag.infrastructure.search.groq_query_rewriter import GroqQueryRewriter


@pytest.mark.live
def test_groq_query_rewriter_live_smoke() -> None:
    """Live smoke test verifying Groq API connectivity and query rewriting.

    This test is excluded from normal deterministic CI runs.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        pytest.skip("GROQ_API_KEY environment variable is not configured.")

    config = load_groq_config_from_env()
    client = GroqSdkChatClient(api_key=config.api_key)
    rewriter = GroqQueryRewriter(config=config, client=client)

    original_text = (
        "How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?"
    )
    question = Question(text=original_text)

    result = rewriter.rewrite(question=question)

    assert isinstance(result, Question)
    assert result.text is not None
    assert len(result.text.strip()) > 0
