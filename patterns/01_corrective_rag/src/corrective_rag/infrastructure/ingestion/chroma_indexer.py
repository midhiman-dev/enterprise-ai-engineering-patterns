"""Chroma vector database indexer for writing document chunks into Chroma collections."""

from typing import Sequence

import chromadb
from chromadb.api.types import EmbeddingFunction

from corrective_rag.infrastructure.ingestion.chunker import DocumentChunk


class ChromaIndexer:
    """Explicit indexing component responsible for indexing DocumentChunks into Chroma.

    Separates write/indexing concerns from read/retrieval concerns.
    """

    def __init__(
        self,
        collection: chromadb.Collection,
    ) -> None:
        """Initialize indexer with a target Chroma collection.

        Args:
            collection: Chroma Collection instance configured for indexing.
        """
        self._collection = collection

    @property
    def collection(self) -> chromadb.Collection:
        """Return the target Chroma collection."""
        return self._collection

    def index_chunks(self, chunks: Sequence[DocumentChunk]) -> int:
        """Upsert a sequence of document chunks into the Chroma collection.

        Args:
            chunks: Sequence of DocumentChunk instances to index.

        Returns:
            Number of chunks successfully indexed.
        """
        if not chunks:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, object]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            # Ensure metadata dict is clean and JSON-serializable for Chroma
            meta_dict = dict(chunk.metadata)
            metadatas.append(meta_dict)

        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)
