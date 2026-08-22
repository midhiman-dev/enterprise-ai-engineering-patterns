"""Infrastructure Search package.

Contains concrete implementations of search-related adapters, including
GroqQueryRewriter for retrieval optimization and future WebSearchProvider implementations.
"""

from corrective_rag.infrastructure.search.groq_query_rewriter import (
    GroqQueryRewriter,
    build_query_rewrite_messages,
)

__all__ = [
    "GroqQueryRewriter",
    "build_query_rewrite_messages",
]
