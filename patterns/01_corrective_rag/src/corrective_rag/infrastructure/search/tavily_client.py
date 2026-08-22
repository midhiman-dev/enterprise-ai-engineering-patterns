"""Tavily Search Client Infrastructure Abstraction.

Provides a narrow internal protocol and official Tavily SDK wrapper client
to isolate network operations and facilitate offline unit testing.
"""

from typing import Any, Protocol

from tavily import TavilyClient

TAVILY_SEARCH_DEPTH = "basic"


class TavilySearchClient(Protocol):
    """Internal infrastructure protocol for Tavily search operations.

    Keeps the Tavily SDK boundary testable via offline fake clients without exposing
    Tavily SDK structures outside the Infrastructure layer.
    """

    def search(self, query: str, max_results: int) -> dict[str, Any]:
        """Executes a search query against Tavily.

        Args:
            query: Exact search query string.
            max_results: Maximum number of candidate results requested.

        Returns:
            Dictionary containing raw provider search results.
        """
        ...


class TavilySdkSearchClient:
    """Concrete implementation of TavilySearchClient using the official Tavily SDK."""

    def __init__(self, api_key: str) -> None:
        """Initializes TavilySdkSearchClient with an official TavilyClient instance.

        Args:
            api_key: Valid secret Tavily API authentication key.
        """
        self._client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int) -> dict[str, Any]:
        """Executes search request using the official Tavily SDK.

        Fixed adapter policy:
            Uses Tavily basic search depth for low-cost, predictable technical documentation retrieval.

        Args:
            query: Exact query string to execute.
            max_results: Max result count constraint.

        Returns:
            Dictionary containing raw Tavily response output.
        """
        return self._client.search(
            query=query,
            max_results=max_results,
            search_depth=TAVILY_SEARCH_DEPTH,
        )
