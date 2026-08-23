"""Application Composition Settings.

Provides application-level configuration choices (e.g. Chroma persistence path,
collection name, retriever top_k) isolated from infrastructure provider configs.
"""

from dataclasses import dataclass
import os

DEFAULT_CHROMA_PATH = "data/chroma"
DEFAULT_CHROMA_COLLECTION = "corrective-rag-kb"
DEFAULT_RETRIEVER_TOP_K = 4


@dataclass(frozen=True)
class ApplicationSettings:
    """Configuration settings for application composition and runtime assembly.

    Attributes:
        chroma_path: Storage directory for persistent Chroma vector database.
        chroma_collection: Target collection name containing indexed document chunks.
        retriever_top_k: Candidate document retrieval limit (must be > 0).
    """

    chroma_path: str = DEFAULT_CHROMA_PATH
    chroma_collection: str = DEFAULT_CHROMA_COLLECTION
    retriever_top_k: int = DEFAULT_RETRIEVER_TOP_K

    def __post_init__(self) -> None:
        """Validates composition settings invariants.

        Raises:
            ValueError: If chroma_path or chroma_collection are blank, or retriever_top_k <= 0.
        """
        if not self.chroma_path or not self.chroma_path.strip():
            raise ValueError("chroma_path cannot be empty.")
        if not self.chroma_collection or not self.chroma_collection.strip():
            raise ValueError("chroma_collection cannot be empty.")
        if self.retriever_top_k <= 0:
            raise ValueError(f"retriever_top_k must be > 0, got {self.retriever_top_k}.")


def load_application_settings_from_env() -> ApplicationSettings:
    """Loads ApplicationSettings from environment variables.

    Environment variables inspected:
        CRAG_CHROMA_PATH: Persistent database path (default: data/chroma).
        CRAG_CHROMA_COLLECTION: Vector collection name (default: corrective-rag-kb).
        CRAG_RETRIEVER_TOP_K: Retrieval candidate limit (default: 4).

    Semantics:
        - Absent environment variable: Uses documented default value.
        - Valid non-blank environment variable: Uses trimmed string value.
        - Explicitly blank or whitespace-only environment variable: Fails fast and raises ValueError.

    Returns:
        Validated ApplicationSettings instance.

    Raises:
        ValueError: If an environment variable is explicitly blank, whitespace-only, or invalid.
    """
    raw_path = os.getenv("CRAG_CHROMA_PATH")
    if raw_path is None:
        chroma_path = DEFAULT_CHROMA_PATH
    else:
        trimmed_path = raw_path.strip()
        if not trimmed_path:
            raise ValueError("CRAG_CHROMA_PATH cannot be blank.")
        chroma_path = trimmed_path

    raw_collection = os.getenv("CRAG_CHROMA_COLLECTION")
    if raw_collection is None:
        chroma_collection = DEFAULT_CHROMA_COLLECTION
    else:
        trimmed_collection = raw_collection.strip()
        if not trimmed_collection:
            raise ValueError("CRAG_CHROMA_COLLECTION cannot be blank.")
        chroma_collection = trimmed_collection

    raw_top_k = os.getenv("CRAG_RETRIEVER_TOP_K")
    if raw_top_k is None:
        top_k = DEFAULT_RETRIEVER_TOP_K
    else:
        trimmed_top_k = raw_top_k.strip()
        if not trimmed_top_k:
            raise ValueError("CRAG_RETRIEVER_TOP_K cannot be blank.")
        try:
            parsed_top_k = int(trimmed_top_k)
        except ValueError as exc:
            raise ValueError(
                f"Invalid CRAG_RETRIEVER_TOP_K: '{raw_top_k}'. Must be a positive integer."
            ) from exc

        if parsed_top_k <= 0:
            raise ValueError(f"retriever_top_k must be > 0, got {parsed_top_k}.")
        top_k = parsed_top_k

    return ApplicationSettings(
        chroma_path=chroma_path,
        chroma_collection=chroma_collection,
        retriever_top_k=top_k,
    )
