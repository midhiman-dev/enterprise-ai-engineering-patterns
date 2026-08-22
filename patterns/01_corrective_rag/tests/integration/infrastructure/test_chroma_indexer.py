"""Integration tests for ChromaIndexer using real ephemeral Chroma client and deterministic test embeddings."""

import chromadb
import pytest

from corrective_rag.infrastructure.embeddings.local_embedding import DeterministicTestEmbeddingFunction
from corrective_rag.infrastructure.ingestion.chunker import DocumentChunk
from corrective_rag.infrastructure.ingestion.chroma_indexer import ChromaIndexer


def test_chroma_indexer_indexes_chunks() -> None:
    client = chromadb.EphemeralClient()
    embedding_fn = DeterministicTestEmbeddingFunction()
    collection = client.create_collection(
        name="test_indexing_coll",
        embedding_function=embedding_fn,
    )

    indexer = ChromaIndexer(collection=collection)

    chunks = [
        DocumentChunk(
            chunk_id="doc1.md::chunk_0",
            content="Kubernetes pod CrashLoopBackOff error details.",
            source="doc1.md",
            chunk_index=0,
            metadata={"source": "doc1.md", "document_title": "CrashLoop Guide"},
        ),
        DocumentChunk(
            chunk_id="doc2.md::chunk_0",
            content="ImagePullBackOff occurs when container image cannot be retrieved.",
            source="doc2.md",
            chunk_index=0,
            metadata={"source": "doc2.md", "document_title": "ImagePull Guide"},
        ),
    ]

    indexed_count = indexer.index_chunks(chunks)
    assert indexed_count == 2
    assert collection.count() == 2


def test_chroma_indexer_empty_chunks() -> None:
    client = chromadb.EphemeralClient()
    embedding_fn = DeterministicTestEmbeddingFunction()
    collection = client.create_collection(
        name="test_empty_indexing_coll",
        embedding_function=embedding_fn,
    )

    indexer = ChromaIndexer(collection=collection)
    assert indexer.index_chunks([]) == 0
    assert collection.count() == 0
