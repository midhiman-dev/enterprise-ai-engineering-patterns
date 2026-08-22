"""Unit tests for TavilyWebSearchProvider infrastructure adapter."""

from typing import Any, Sequence

import pytest

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.domain.ports.web_search_provider import WebSearchProvider
from corrective_rag.infrastructure.search.tavily_config import TavilyConfig
from corrective_rag.infrastructure.search.tavily_web_search_provider import (
    TavilyWebSearchProvider,
)


class FakeTavilySearchClient:
    """Handwritten fake client for offline testing of TavilyWebSearchProvider."""

    def __init__(
        self,
        response: dict[str, Any] | None = None,
        raise_exc: Exception | None = None,
    ) -> None:
        self.response = response if response is not None else {"results": []}
        self.raise_exc = raise_exc
        self.last_query: str | None = None
        self.last_max_results: int | None = None

    def search(self, query: str, max_results: int) -> dict[str, Any]:
        self.last_query = query
        self.last_max_results = max_results
        if self.raise_exc:
            raise self.raise_exc
        return self.response


def test_tavily_web_search_provider_protocol_conformance() -> None:
    """Verifies TavilyWebSearchProvider satisfies WebSearchProvider protocol signature."""
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient()
    provider: WebSearchProvider = TavilyWebSearchProvider(config, client)
    assert callable(provider.search)


def test_maps_one_tavily_result_to_domain_document() -> None:
    """Verifies single Tavily search result is mapped to Domain Document entity."""
    fake_response = {
        "results": [
            {
                "title": "Pod Lifecycle",
                "url": "https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/",
                "content": "A Pod lifecycle passes through various phases including Pending, Running, and Succeeded.",
                "score": 0.91,
            }
        ]
    }
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient(response=fake_response)
    provider = TavilyWebSearchProvider(config, client)

    question = Question(text="Kubernetes Pod lifecycle phases")
    docs = provider.search(question)

    assert len(docs) == 1
    doc = docs[0]
    assert isinstance(doc, Document)
    assert doc.content == "A Pod lifecycle passes through various phases including Pending, Running, and Succeeded."
    assert doc.source == "https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"
    assert doc.title == "Pod Lifecycle"
    assert doc.source_url == "https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"
    assert doc.metadata.get("tavily_score") == 0.91


def test_maps_multiple_results_preserving_order() -> None:
    """Verifies multiple Tavily results are mapped to Domain Documents in provider order."""
    fake_response = {
        "results": [
            {
                "title": "Doc 1",
                "url": "https://example.com/1",
                "content": "First result content",
                "score": 0.95,
            },
            {
                "title": "Doc 2",
                "url": "https://example.com/2",
                "content": "Second result content",
                "score": 0.85,
            },
            {
                "title": "Doc 3",
                "url": "https://example.com/3",
                "content": "Third result content",
                "score": 0.75,
            },
        ]
    }
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient(response=fake_response)
    provider = TavilyWebSearchProvider(config, client)

    docs = provider.search(Question(text="multidoc test"))
    assert len(docs) == 3
    assert [d.title for d in docs] == ["Doc 1", "Doc 2", "Doc 3"]
    assert [d.source for d in docs] == [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3",
    ]


def test_search_uses_question_text_exactly() -> None:
    """Verifies search forwards Question.text without query modification."""
    query_text = "Kubernetes 1.32 node-pressure eviction policy"
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient()
    provider = TavilyWebSearchProvider(config, client)

    provider.search(Question(text=query_text))
    assert client.last_query == query_text


def test_max_results_forwarded_from_config() -> None:
    """Verifies configured max_results is passed to search client."""
    config = TavilyConfig(api_key="tvly-test-key", max_results=3)
    client = FakeTavilySearchClient()
    provider = TavilyWebSearchProvider(config, client)

    provider.search(Question(text="test query"))
    assert client.last_max_results == 3


def test_empty_search_results_returns_empty_list() -> None:
    """Verifies empty search results dictionary returns an empty list without raising."""
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient(response={"results": []})
    provider = TavilyWebSearchProvider(config, client)

    docs = provider.search(Question(text="nonexistent query"))
    assert docs == []


def test_skips_malformed_and_blank_content_results() -> None:
    """Verifies results with missing or blank content or URL are skipped."""
    fake_response = {
        "results": [
            {
                "title": "Blank Content",
                "url": "https://example.com/blank",
                "content": "   ",
            },
            {
                "title": "Missing URL",
                "url": "",
                "content": "Valid content but no URL",
            },
            {
                "title": "Valid Result",
                "url": "https://example.com/valid",
                "content": "Valid content and valid URL",
            },
        ]
    }
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient(response=fake_response)
    provider = TavilyWebSearchProvider(config, client)

    docs = provider.search(Question(text="malformed test"))
    assert len(docs) == 1
    assert docs[0].title == "Valid Result"
    assert docs[0].source == "https://example.com/valid"


def test_provider_failure_raises_runtime_error_with_cause() -> None:
    """Verifies provider exceptions raise RuntimeError('Tavily search request failed.') preserving cause."""
    simulated_error = RuntimeError("simulated rate limit")
    config = TavilyConfig(api_key="tvly-test-key")
    client = FakeTavilySearchClient(raise_exc=simulated_error)
    provider = TavilyWebSearchProvider(config, client)

    with pytest.raises(RuntimeError, match="^Tavily search request failed\\.$") as exc_info:
        provider.search(Question(text="failing search"))

    assert exc_info.value.__cause__ is simulated_error
    assert "simulated rate limit" not in str(exc_info.value)
