"""Infrastructure Search package.

Contains concrete implementations of search-related adapters, including
GroqQueryRewriter for retrieval optimization and TavilyWebSearchProvider for
external corrective web search.
"""

from corrective_rag.infrastructure.search.groq_query_rewriter import (
    GroqQueryRewriter,
    build_query_rewrite_messages,
)
from corrective_rag.infrastructure.search.tavily_client import (
    TAVILY_SEARCH_DEPTH,
    TavilySdkSearchClient,
    TavilySearchClient,
)
from corrective_rag.infrastructure.search.tavily_config import (
    DEFAULT_TAVILY_MAX_RESULTS,
    TavilyConfig,
    load_tavily_config_from_env,
)
from corrective_rag.infrastructure.search.tavily_web_search_provider import (
    TavilyWebSearchProvider,
)

__all__ = [
    "DEFAULT_TAVILY_MAX_RESULTS",
    "GroqQueryRewriter",
    "TAVILY_SEARCH_DEPTH",
    "TavilyConfig",
    "TavilySdkSearchClient",
    "TavilySearchClient",
    "TavilyWebSearchProvider",
    "build_query_rewrite_messages",
    "load_tavily_config_from_env",
]
