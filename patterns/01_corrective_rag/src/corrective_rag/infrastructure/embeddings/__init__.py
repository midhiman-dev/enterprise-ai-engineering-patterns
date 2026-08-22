"""Infrastructure embeddings package providing local and test embedding functions."""

from corrective_rag.infrastructure.embeddings.local_embedding import (
    DefaultLocalEmbeddingFunction,
    DeterministicTestEmbeddingFunction,
)

__all__ = [
    "DeterministicTestEmbeddingFunction",
    "DefaultLocalEmbeddingFunction",
]
