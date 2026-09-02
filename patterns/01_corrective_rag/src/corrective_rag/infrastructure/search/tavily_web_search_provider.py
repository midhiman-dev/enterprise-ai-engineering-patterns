"""Tavily Web Search Infrastructure Adapter.

Implements external web evidence retrieval using the Tavily Search API.
Structurally satisfies the Domain WebSearchProvider port without exposing Tavily
SDK objects, response models, or API mechanics outside the Infrastructure layer.

Security boundary:
    Search-provider results are external, untrusted content. Only results whose URLs
    match configured authoritative source prefixes are admitted into the Domain
    evidence set. Accepted web documents are explicitly tagged with provenance and
    trust metadata so downstream components can preserve the distinction between
    trusted instructions and untrusted retrieved data.
"""

from collections.abc import Sequence

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.search.tavily_client import TavilySearchClient
from corrective_rag.infrastructure.search.tavily_config import TavilyConfig

EXTERNAL_RETRIEVAL_CHANNEL = "external_web"
ALLOWLISTED_SOURCE_TRUST = "allowlisted_authoritative"
SOURCE_POLICY_NAME = "authoritative_source_prefix_allowlist"


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

    def _is_allowed_source(self, url: str) -> bool:
        """Return True only when URL matches an explicitly configured source prefix."""
        return any(
            url.startswith(prefix) for prefix in self._config.allowed_source_prefixes
        )

    def search(self, question: Question) -> Sequence[Document]:
        """Search authoritative external sources and return normalized Domain Documents.

        External search results are treated as untrusted content even when their source
        is allowlisted. The allowlist establishes source authority; it does not grant
        instruction authority to the retrieved text.

        Args:
            question: Question entity containing the search query string.

        Returns:
            An ordered sequence of allowlisted candidate Domain Document entities.

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

            # Deterministic control: external evidence crosses the trust boundary only
            # when it originates from a configured authoritative source prefix.
            if not self._is_allowed_source(url):
                continue

            raw_title = item.get("title")
            title = raw_title.strip() if isinstance(raw_title, str) and raw_title.strip() else None

            metadata: dict[str, object] = {
                "retrieval_channel": EXTERNAL_RETRIEVAL_CHANNEL,
                "source_trust": ALLOWLISTED_SOURCE_TRUST,
                "source_policy": SOURCE_POLICY_NAME,
            }
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
