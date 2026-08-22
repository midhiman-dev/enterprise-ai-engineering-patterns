"""Integration tests for ChromaRetriever adapter using real ephemeral Chroma client and test embeddings."""

import chromadb
import pytest

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from corrective_rag.infrastructure.embeddings.local_embedding import DeterministicTestEmbeddingFunction
from corrective_rag.infrastructure.ingestion.chunker import DocumentChunk
from corrective_rag.infrastructure.ingestion.chroma_indexer import ChromaIndexer
from corrective_rag.infrastructure.retrieval.chroma_retriever import ChromaRetriever


@pytest.fixture
def ephemeral_collection(request: pytest.FixtureRequest) -> chromadb.Collection:
    client = chromadb.EphemeralClient()
    embedding_fn = DeterministicTestEmbeddingFunction()
    return client.create_collection(
        name=request.node.name.replace("[", "_").replace("]", "_"),
        embedding_function=embedding_fn,
    )


def test_retriever_index_and_retrieve(ephemeral_collection: chromadb.Collection) -> None:
    indexer = ChromaIndexer(collection=ephemeral_collection)
    chunks = [
        DocumentChunk(
            chunk_id="crashloop.md::chunk_0",
            content="CrashLoopBackOff indicates that a Kubernetes pod repeatedly starts, crashes, and attempts to restart. Inspect logs with kubectl logs.",
            source="crashloop.md",
            chunk_index=0,
            metadata={"source": "crashloop.md", "document_title": "CrashLoopBackOff Guide"},
        ),
        DocumentChunk(
            chunk_id="dns.md::chunk_0",
            content="CoreDNS service resolution troubleshooting guide for cluster IP connectivity.",
            source="dns.md",
            chunk_index=0,
            metadata={"source": "dns.md", "document_title": "CoreDNS Guide"},
        ),
    ]
    indexer.index_chunks(chunks)

    retriever = ChromaRetriever(collection=ephemeral_collection, top_k=4)
    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    results = retriever.retrieve(question)

    assert len(results) >= 1
    # Check returned objects are Domain Document entities
    for doc in results:
        assert isinstance(doc, Document)

    # Relevant content must be among retrieved candidates
    content_concat = " ".join([d.content for d in results])
    assert "CrashLoopBackOff" in content_concat

    # Provenance survives round trip
    matching_doc = next(d for d in results if "CrashLoopBackOff" in d.content)
    assert matching_doc.source == "crashloop.md"
    assert matching_doc.title == "CrashLoopBackOff Guide"


def test_retriever_top_k_constraint(ephemeral_collection: chromadb.Collection) -> None:
    indexer = ChromaIndexer(collection=ephemeral_collection)
    chunks = [
        DocumentChunk(
            chunk_id=f"doc{i}.md::chunk_0",
            content=f"Kubernetes cluster troubleshooting topic item number {i}",
            source=f"doc{i}.md",
            chunk_index=0,
            metadata={"source": f"doc{i}.md"},
        )
        for i in range(10)
    ]
    indexer.index_chunks(chunks)

    retriever = ChromaRetriever(collection=ephemeral_collection, top_k=2)
    question = Question(text="Kubernetes cluster troubleshooting topic")
    results = retriever.retrieve(question)

    assert len(results) <= 2


def test_retriever_empty_collection(ephemeral_collection: chromadb.Collection) -> None:
    retriever = ChromaRetriever(collection=ephemeral_collection, top_k=4)
    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    results = retriever.retrieve(question)

    assert results == []


def test_retriever_metadata_preservation(ephemeral_collection: chromadb.Collection) -> None:
    indexer = ChromaIndexer(collection=ephemeral_collection)
    chunk = DocumentChunk(
        chunk_id="meta.md::chunk_3",
        content="Document with detailed provenance metadata.",
        source="meta.md",
        chunk_index=3,
        metadata={"source": "meta.md", "chunk_index": 3, "document_title": "Meta Title"},
    )
    indexer.index_chunks([chunk])

    retriever = ChromaRetriever(collection=ephemeral_collection, top_k=4)
    question = Question(text="provenance metadata")
    results = retriever.retrieve(question)

    assert len(results) == 1
    doc = results[0]
    assert doc.source == "meta.md"
    assert doc.title == "Meta Title"
    assert doc.metadata["chunk_index"] == 3
    assert "retrieval_distance" in doc.metadata
