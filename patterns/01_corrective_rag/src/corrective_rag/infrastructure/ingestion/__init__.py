"""Document ingestion infrastructure module for loading, chunking, and indexing KB documents."""

from corrective_rag.infrastructure.ingestion.chunker import DocumentChunk, DocumentChunker
from corrective_rag.infrastructure.ingestion.chroma_indexer import ChromaIndexer
from corrective_rag.infrastructure.ingestion.document_loader import (
    SourceDocument,
    load_documents_from_directory,
)

__all__ = [
    "SourceDocument",
    "load_documents_from_directory",
    "DocumentChunk",
    "DocumentChunker",
    "ChromaIndexer",
]
