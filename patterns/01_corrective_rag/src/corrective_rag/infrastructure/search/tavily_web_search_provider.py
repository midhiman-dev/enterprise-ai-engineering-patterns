"""Tavily Web Search Infrastructure Adapter.

Implements external web evidence retrieval using the Tavily Search API.
Structurally satisfies the Domain WebSearchProvider port without exposing Tavily
SDK objects, response models, or API mechanics outside the Infrastructure layer.

Learner Diagnostic Questions Answered:
1. What does this file do?
   Executes external web searches via Tavily and normalizes provider result payloads
   into provider-neutral Domain Document entities.
2. Why does it belong in this architectural layer?
   It is an Infrastructure adapter implementing the Domain WebSearchProvider port.
3. What dependency does it need?
   Requires TavilyConfig, TavilySearchClient, and Domain Question / Document entities.
4. What would change if that dependency were replaced?
   Replacing Tavily with another search provider (e.g., Bing or SerpAPI) would replace
   this file without altering Domain ports or LangGraph orchestration nodes.
"""

from collections.abc import Sequence

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.search.tavily_client import TavilySearchClient
from corrective_rag.infrastructure.search.tavily_config import TavilyConfig


class TavilyWebSearchProvider:
    """Concrete Tavily implementation of the Domain WebSearchProvider port.

    Structurally satisfies the WebSearchProvider Protocol without explicit inheritance.
    """

    def __init__(self, config: TavilyConfig, client: TavilySearchClient) -> None:
        """Initializes TavilyWebSearchProvider adapter.

        Args:
            config: Validated Tavily infrastructure configuration.
            client: Injected Tavily search client interface.
        """
        self._config = config
        self._client = client

    def search(self, question: Question) -> Sequence[Document]:
        """Searches external web sources via Tavily and returns normalized Domain Documents.

        Args:
            question: Question entity containing the search query string.

        Returns:
            An ordered sequence of candidate Domain Document entities.

        Raises:
            RuntimeError: If Tavily API request fails due to operational network, rate-limit,
                or authentication errors.
        """
        try:
            raw_response = self._client.search(
                query=question.text,
                max_results=self._config.max_results,
            )
        except Exception as exc:
            raise RuntimeError("Tavily search request failed.") from exc

        if not raw_response or not isinstance(raw_response, dict):
            return []

        raw_results = raw_response.get("results")
        if not raw_results or not isinstance(raw_results, list):
            return []

        documents: list[Document] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue

            raw_content = item.get("content")
            if not raw_content or not isinstance(raw_content, str) or not raw_content.strip():
                continue

            raw_url = item.get("url")
            if not raw_url or not isinstance(raw_url, str) or not raw_url.strip():
                continue

            content = raw_content.strip()
            url = raw_url.strip()

            raw_title = item.get("title")
            title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else None

            metadata: dict[str, object] = {}
            raw_score = item.get("score")
            if isinstance(raw_score, (int, float)):
                metadata["tavily_score"] = float(raw_score)

            doc = Document(
                content=content,
                source=url,
                title=title,
                source_url=url,
                metadata=metadata,
            )
            documents.append(doc)

        return documents
