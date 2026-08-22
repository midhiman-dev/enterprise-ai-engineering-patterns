# Use Case 01 — Step-by-Step Tutorial

> **Current Status:** 🟢 **Pass-6 Implemented.** Local KB document loading (`DocumentLoader`), paragraph/character-aware chunking (`DocumentChunker`), local embeddings (`DeterministicTestEmbeddingFunction`, `DefaultLocalEmbeddingFunction`), Chroma vector store indexing (`ChromaIndexer`), and concrete `ChromaRetriever` adapter implementing the `Retriever` domain port are fully implemented and verified with offline integration tests. Knowledge-base fixture (`data/kb_snapshot/`), build script (`scripts/build_kb_index.py`), and ADR-002 are complete.


## Overview

This tutorial will walk learners through building Use Case 01 (Corrective RAG for Kubernetes Troubleshooting) step by step.

In accordance with repository guidelines:
* All tutorial code snippets will be taken directly from, or accurately synchronized with, verified repository code.
* No simplified pseudo-code that materially differs from the verified solution will be introduced.

## Planned Learning & Build Sequence

The tutorial follows a deliberate learning sequence designed to isolate framework orchestration mechanics from third-party API integration complexity:

1. **Problem & Core Concepts** — The stale Kubernetes knowledge base failure mode.
2. **Domain Entities** — `Question`, `Document`, `GradedDocument`, `Answer`, `DecisionTrace`. (Implemented)
3. **Domain Ports** — Provider-neutral capability contracts (`Retriever`, `RelevanceGrader`, `QueryRewriter`, `Generator`, `WebSearchProvider`, `HallucinationChecker`, `DecisionTraceRepository`) defined using `typing.Protocol`. (Implemented)
4. **LangGraph State & Straight Workflow** — Defining graph state schema, node handlers, workflow dependency container, and straight graph compilation. (Implemented)
5. **Handwritten Fakes** — Controlled in-memory fakes for testing workflow routing without external network calls. (Implemented)
6. **Straight-Path Routing Unit Tests** — Testing the straight-through graph execution path deterministically using handwritten fakes. (Implemented)
7. **Query Rewriting & Web Search Routing** — Adding stale-KB detection and web fallback routing branches. (Implemented)
8. **Bounded Grounding Retry & Safe Refusal** — Adding bounded generation retries and safe refusal routing for ungrounded answers. (Implemented)
9. **Chroma Retrieval Adapter** — Concrete vector store implementation of the `Retriever` port (`ChromaRetriever`, `ChromaIndexer`, `DocumentChunker`, `DocumentLoader`). (Implemented)
10. **OpenAI / Ollama AI Adapters** — Concrete LLM implementations of `Generator`, `RelevanceGrader`, and `HallucinationChecker`.
11. **Tavily Web Search Adapter** — Concrete implementation of `WebSearchProvider`.
12. **Decision Trace Persistence** — SQLite storage implementation of `DecisionTraceRepository`.
13. **Composition Root** — Assembling graph orchestration with concrete adapters.
14. **FastAPI / Interface** — Exposing HTTP/SSE endpoints for query processing and decision trace inspection.
15. **Integration & Golden Acceptance Tests** — Running golden queries against full adapter stack.
16. **Decision Trace Inspection** — Auditing system decisions across local vs. web fallback routes.
17. **Production Evolution & Interview Lessons** — System design trade-offs and scaling strategies.

---

## Pass-6 Learning Outline — Ingestion & Chroma Retrieval

Pass-6 demonstrates how source documents travel through the local ingestion and vector retrieval pipeline:

```text
source documents
      ↓
document loader
      ↓
chunker (chunk_size, chunk_overlap)
      ↓
embedding function
      ↓
index in Chroma collection
      ↓
semantic query
      ↓
top-k candidate matches
      ↓
provider-neutral Domain Document[]
```

### Key Technical Concepts
* **Source Document vs. Chunk**: Raw source files (`data/kb_snapshot/*.md`) are high-level units of knowledge. They must be split into bounded text chunks before embedding because vector distance calculations perform poorly over multi-page texts with disparate topics.
* **Chunk Size & Overlap**: `chunk_size` defines the upper character bound for semantic focus, while `chunk_overlap` preserves context continuity across adjacent chunk boundaries.
* **Deterministic Chunk Identifiers**: Each chunk receives a stable ID (`<source>::chunk_<index>`), ensuring idempotent and repeatable vector store indexing runs.
* **Candidate Retrieval vs. Relevance Grading**: `ChromaRetriever.retrieve()` performs *candidate selection* based on nearest-neighbor vector distance in semantic embedding space. It retrieves the top `top_k` candidate chunks. Vector distance alone is not proof of factual relevance for answering the question—which is why the downstream `RelevanceGrader` node still evaluates candidates against the question.

---

## Interview Guide — Candidate Retrieval Failures

> **Interview Question:** What if the correct document exists in the knowledge base, but vector retrieval fails to return it?

### Diagnostic Sequence
1. **Ingestion Verification**: Is the source document actually ingested in the target Chroma collection?
2. **Chunking Strategy**: Was the critical fact split across a chunk boundary or truncated by chunk size limits?
3. **Embedding Representation**: Did the vector embedding capture the domain-specific terms (e.g. `CrashLoopBackOff`, error codes)?
4. **Top-K Parameter**: Was `top_k` set too low (e.g., `top_k=2` when relevant evidence ranked 3rd or 4th)?
5. **Metadata Filters**: Were metadata filters mistakenly excluding valid document categories?
6. **Hybrid Retrieval**: Would combining vector search with BM25 keyword matching improve recall for exact technical terms?
7. **Cross-Encoder Reranking**: Would a cross-encoder reranker placed after candidate retrieval improve document ordering?
8. **Evaluation Benchmarks**: Is retrieval recall being measured explicitly using hit-rate or MRR metrics on golden evaluation datasets?

---

## Architecture Scaling Note — Ingestion at 100,000 Documents

> *Design-only — not implemented in Pass-6*

How would this ingestion and retrieval architecture evolve from a small local test fixture to an enterprise dataset of 100,000+ documents?

1. **Distributed Asynchronous Ingestion**: Replace sequential script execution (`build_kb_index.py`) with background worker queues (e.g. Celery / Kafka) processing document loading, chunking, and embedding in parallel.
2. **Incremental Indexing & Change Data Capture**: Track document file hashes / timestamps so only updated or added documents trigger re-chunking and re-embedding.
3. **Distributed Vector Database**: Migrate from single-node local disk Chroma to distributed cluster deployments (e.g., Milvus, Qdrant, Pinecone, or PostgreSQL with `pgvector`).
4. **Hybrid Lexical + Dense Retrieval**: Combine dense semantic embeddings with sparse BM25 indexing (e.g. Elasticsearch / Meilisearch) to capture both semantic intent and exact technical error codes.
5. **Two-Stage Retrieval & Reranking**: Retrieve top 50–100 candidates via fast vector/hybrid search, then pass candidate pairs to a Cohere / BGE cross-encoder reranker to pick the top 4–6 highest-quality documents for LLM context generation.
