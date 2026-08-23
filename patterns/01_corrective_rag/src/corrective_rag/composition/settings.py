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

    Returns:
        Validated ApplicationSettings instance.

    Raises:
        ValueError: If environment variable values violate configuration invariants.
    """
    raw_path = os.getenv("CRAG_CHROMA_PATH")
    chroma_path = raw_path.strip() if raw_path and raw_path.strip() else DEFAULT_CHROMA_PATH

    raw_collection = os.getenv("CRAG_CHROMA_COLLECTION")
    chroma_collection = (
        raw_collection.strip()
        if raw_collection and raw_collection.strip()
        else DEFAULT_CHROMA_COLLECTION
    )

    top_k = DEFAULT_RETRIEVER_TOP_K
    raw_top_k = os.getenv("CRAG_RETRIEVER_TOP_K")
    if raw_top_k and raw_top_k.strip():
        try:
            parsed_top_k = int(raw_top_k.strip())
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
