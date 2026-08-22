"""Document chunker for breaking source documents into overlapping indexable chunks."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

from corrective_rag.infrastructure.ingestion.document_loader import SourceDocument

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a bounded text chunk extracted from a source document.

    Attributes:
        chunk_id: Deterministic identifier for vector store indexing.
        content: Text content of the chunk.
        source: Provenance identifier matching the original SourceDocument.
        chunk_index: 0-indexed position of chunk within its source document.
        metadata: Metadata mapping preserving document title and provenance.
    """

    chunk_id: str
    content: str
    source: str
    chunk_index: int
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("DocumentChunk chunk_id cannot be empty.")
        if not self.content or not self.content.strip():
            raise ValueError("DocumentChunk content cannot be empty.")
        if not self.source or not self.source.strip():
            raise ValueError("DocumentChunk source cannot be empty.")
        if self.chunk_index < 0:
            raise ValueError("DocumentChunk chunk_index cannot be negative.")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


class DocumentChunker:
    """Paragraph and character-aware text chunker.

    Splits SourceDocument content into chunks governed by chunk_size and chunk_overlap
    while preserving provenance metadata and generating deterministic chunk IDs.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize DocumentChunker with explicit size and overlap parameters.

        Args:
            chunk_size: Maximum character length per chunk (must be > 0).
            chunk_overlap: Overlapping character count between adjacent chunks (must be >= 0 and < chunk_size).

        Raises:
            ValueError: If configuration parameters violate chunking invariants.
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be > 0, got {chunk_size}.")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be >= 0, got {chunk_overlap}.")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})."
            )

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    @property
    def chunk_size(self) -> int:
        """Return configured max chunk size."""
        return self._chunk_size

    @property
    def chunk_overlap(self) -> int:
        """Return configured chunk overlap."""
        return self._chunk_overlap

    def chunk_document(self, document: SourceDocument) -> Sequence[DocumentChunk]:
        """Split a SourceDocument into a sequence of DocumentChunk instances.

        Args:
            document: Source document to split.

        Returns:
            Sequence of DocumentChunk instances. Blank/empty input returns an empty sequence.
        """
        text = document.content.strip()
        if not text:
            return []

        # If entire document fits in one chunk
        if len(text) <= self._chunk_size:
            chunk_id = self._generate_chunk_id(document.source, 0)
            chunk_metadata = self._build_metadata(document, 0)
            return [
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=text,
                    source=document.source,
                    chunk_index=0,
                    metadata=chunk_metadata,
                )
            ]

        chunks: list[DocumentChunk] = []
        start = 0
        text_length = len(text)
        chunk_index = 0
        step = self._chunk_size - self._chunk_overlap

        while start < text_length:
            end = start + self._chunk_size
            chunk_text = text[start:end]

            # If not at the end of the text, attempt to break at line or space boundary
            if end < text_length:
                last_newline = chunk_text.rfind("\n")
                if last_newline > self._chunk_size // 2:
                    chunk_text = chunk_text[: last_newline + 1]
                else:
                    last_space = chunk_text.rfind(" ")
                    if last_space > self._chunk_size // 2:
                        chunk_text = chunk_text[: last_space + 1]

            cleaned_chunk_text = chunk_text.strip()
            if cleaned_chunk_text:
                chunk_id = self._generate_chunk_id(document.source, chunk_index)
                chunk_metadata = self._build_metadata(document, chunk_index)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        content=cleaned_chunk_text,
                        source=document.source,
                        chunk_index=chunk_index,
                        metadata=chunk_metadata,
                    )
                )
                chunk_index += 1

            start += len(chunk_text) - self._chunk_overlap if len(chunk_text) > self._chunk_overlap else step

        return chunks

    def _generate_chunk_id(self, source: str, chunk_index: int) -> str:
        """Generate a deterministic chunk ID based on source identity and chunk index."""
        return f"{source}::chunk_{chunk_index}"

    def _build_metadata(self, document: SourceDocument, chunk_index: int) -> dict[str, object]:
        """Construct provenance metadata dictionary for a chunk."""
        meta: dict[str, object] = {
            "source": document.source,
            "chunk_index": chunk_index,
        }
        if "document_title" in document.metadata:
            meta["document_title"] = document.metadata["document_title"]
        return meta
