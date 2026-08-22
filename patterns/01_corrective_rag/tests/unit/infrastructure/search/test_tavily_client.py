"""Unit tests for Tavily SDK client wrapper and adapter policy."""

from unittest.mock import MagicMock, patch

from corrective_rag.infrastructure.search.tavily_client import (
    TAVILY_SEARCH_DEPTH,
    TavilySdkSearchClient,
)


def test_tavily_sdk_search_client_uses_basic_search_depth_policy() -> None:
    """Verifies TavilySdkSearchClient passes fixed basic search depth policy to TavilyClient."""
    with patch("corrective_rag.infrastructure.search.tavily_client.TavilyClient") as mock_tavily_cls:
        mock_instance = MagicMock()
        mock_instance.search.return_value = {"results": []}
        mock_tavily_cls.return_value = mock_instance

        client = TavilySdkSearchClient(api_key="tvly-test-key")
        client.search(query="kubernetes pod eviction", max_results=5)

        mock_instance.search.assert_called_once_with(
            query="kubernetes pod eviction",
            max_results=5,
            search_depth=TAVILY_SEARCH_DEPTH,
        )
