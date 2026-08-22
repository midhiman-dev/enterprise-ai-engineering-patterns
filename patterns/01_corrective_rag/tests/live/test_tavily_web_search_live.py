"""Opt-in live integration smoke test for TavilyWebSearchProvider.

Requires TAVILY_API_KEY environment variable.
Excluded from standard offline unit test suites via `@pytest.mark.live`.
"""

import os

import pytest

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.search.tavily_client import TavilySdkSearchClient
from corrective_rag.infrastructure.search.tavily_config import (
    load_tavily_config_from_env,
)
from corrective_rag.infrastructure.search.tavily_web_search_provider import (
    TavilyWebSearchProvider,
)


@pytest.mark.live
def test_tavily_web_search_live_smoke() -> None:
    """Executes a single live web search query against the official Tavily API.

    Verifies live Tavily responses map cleanly into Domain Document entities.
    """
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("TAVILY_API_KEY", "").strip():
        pytest.skip("TAVILY_API_KEY environment variable not set. Skipping live test.")

    config = load_tavily_config_from_env()
    client = TavilySdkSearchClient(api_key=config.api_key)
    provider = TavilyWebSearchProvider(config=config, client=client)

    question = Question(text="Kubernetes CrashLoopBackOff troubleshooting documentation")
    documents = provider.search(question)

    assert isinstance(documents, (list, tuple))
    assert len(documents) > 0, "Expected at least one web search document from Tavily live search."

    for doc in documents:
        assert isinstance(doc, Document)
        assert doc.content and doc.content.strip()
        assert doc.source and doc.source.strip()
