"""Local embedding implementations for Chroma integration and offline testing."""

import hashlib
import math
from typing import Sequence

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions


class DeterministicTestEmbeddingFunction(EmbeddingFunction[Documents]):
    """Offline, deterministic embedding function designed for fast integration testing.

    Converts input text documents into fixed-dimension L2-normalized float vectors using
    SHA-256 token hashing. Requires zero network calls, zero API keys, and zero external
    model downloads, guaranteeing fast and reliable CI environment execution.
    """

    def __init__(self, dimension: int = 32) -> None:
        """Initialize test embedding function with explicit vector dimension.

        Args:
            dimension: Dimensionality of output vectors (default: 32).
        """
        if dimension <= 0:
            raise ValueError(f"Embedding dimension must be > 0, got {dimension}.")
        self._dimension = dimension

    def name(self) -> str:
        """Return identifier for embedding function."""
        return "deterministic_test_embedding"

    def get_config(self) -> dict[str, object]:
        """Return configuration dictionary for Chroma serialization."""
        return {"dimension": self._dimension}

    def __call__(self, input: Documents) -> Embeddings:
        """Generate deterministic L2-normalized embedding vectors for input texts.

        Args:
            input: Sequence of document texts.

        Returns:
            List of float vector embeddings.
        """
        embeddings: list[list[float]] = []

        for text in input:
            vector = [0.0] * self._dimension
            tokens = text.lower().split()
            if not tokens:
                embeddings.append(vector)
                continue

            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                for i in range(self._dimension):
                    # Distribute hash bytes across vector dimensions
                    val = (digest[i % len(digest)] - 128) / 128.0
                    vector[i] += val

            # Normalize to L2 unit vector
            sq_sum = sum(v * v for v in vector)
            if sq_sum > 0:
                magnitude = math.sqrt(sq_sum)
                vector = [v / magnitude for v in vector]

            embeddings.append(vector)

        return embeddings


class DefaultLocalEmbeddingFunction(EmbeddingFunction[Documents]):
    """Local semantic embedding function wrapper for local knowledge-base indexing script.

    Uses Chroma's default ONNX-based MiniLM embedding model. Fails fast with an explicit
    RuntimeError if the semantic embedding model fails to initialize or execute.

    Note on Embedding-Space Consistency:
        The same embedding model and configuration must be used for both indexing and querying
        a collection. Changing embedding models requires controlled re-embedding and re-indexing
        rather than silently mixing incompatible vector spaces.
    """

    def __init__(self) -> None:
        try:
            self._chroma_ef = embedding_functions.DefaultEmbeddingFunction()
        except Exception as exc:
            raise RuntimeError(
                "Local semantic embedding model could not be loaded. "
                "Ensure the required Chroma embedding model is available before building or querying this index."
            ) from exc

    def name(self) -> str:
        """Return identifier for embedding function."""
        return "default_local_semantic_embedding"

    def get_config(self) -> dict[str, object]:
        """Return configuration dictionary for Chroma serialization."""
        return {}

    def __call__(self, input: Documents) -> Embeddings:
        try:
            return self._chroma_ef(input)
        except Exception as exc:
            raise RuntimeError(
                "Local semantic embedding model execution failed for input documents."
            ) from exc
