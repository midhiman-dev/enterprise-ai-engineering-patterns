# Use Case 01 — Step-by-Step Tutorial

> **Current Status:** 🟢 **Pass-7 Implemented.** Groq hosted LLM generation infrastructure adapter (`GroqGenerator`), configuration model/loader (`GroqConfig`, `load_groq_config_from_env`), internal client protocol and wrapper (`GroqChatClient`, `GroqSdkChatClient`), prompt message construction (`build_generation_messages`), offline unit tests with handwritten fake client, opt-in live smoke test (`test_groq_generator_live.py`), and ADR-003 are complete and verified.


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
10. **Groq Generator Adapter** — Concrete hosted LLM implementation of the `Generator` domain port (`GroqGenerator`, `GroqConfig`, `GroqChatClient`, `GroqSdkChatClient`). (Implemented)
11. **Groq Relevance Grader** — Concrete implementation of `RelevanceGrader`.
12. **Groq Query Rewriter** — Concrete implementation of `QueryRewriter`.
13. **Groq Hallucination Checker** — Concrete implementation of `HallucinationChecker`.
14. **Tavily Web Search Adapter** — Concrete implementation of `WebSearchProvider`.
15. **Decision Trace Persistence** — SQLite storage implementation of `DecisionTraceRepository`.
16. **Composition Root** — Assembling graph orchestration with concrete adapters.
17. **FastAPI / Interface** — Exposing HTTP/SSE endpoints for query processing and decision trace inspection.
18. **Integration & Golden Acceptance Tests** — Running golden queries against full adapter stack.
19. **Decision Trace Inspection** — Auditing system decisions across local vs. web fallback routes.
20. **Production Evolution & Interview Lessons** — System design trade-offs and scaling strategies.


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

---

## Interview Guide — What Happens If the Embedding Model Changes?

> **Interview Question:** How do you handle changing or upgrading an embedding model in a production RAG system?

Changing an embedding model in production requires a controlled migration strategy because vector representations across different embedding models inhabit incompatible mathematical vector spaces:

1. **Embedding Space Compatibility**: Index-time embeddings and query-time embeddings must always use the exact same embedding model and configuration. Vector distances between different embedding spaces are meaningless.
2. **Re-Embedding Corpus**: Upgrading or switching an embedding model requires re-embedding and re-indexing the entire document corpus into a new versioned vector collection (e.g. `corrective-rag-kb-v2`).
3. **Versioned Indexing**: Build the replacement vector collection in parallel while the existing production index continues serving user queries.
4. **Retrieval Evaluation**: Run evaluation benchmarks (MRR, Hit@K) against a golden evaluation dataset using the new index before cutting over production traffic.
5. **Zero-Downtime Cutover & Rollback**: Update the retrieval adapter configuration to point to the new collection while retaining the old index for immediate rollback capabilities.

> *Design guidance — not implemented in Pass-6A*

---

## Pass-7 Learning Outline — Groq Generator Infrastructure

Pass-7 demonstrates how candidate generation is implemented behind the Domain `Generator` port using the Groq hosted LLM provider:

```text
Domain Question + Document[]
      ↓
GroqGenerator (Prompt Construction)
      ↓
GroqChatClient (Infrastructure Protocol)
      ↓
GroqSdkChatClient (Groq SDK)
      ↓
Domain Answer (AnswerStatus.ANSWERED)
```

### Key Technical Concepts & Learner Takeaways

1. **Offline-First Testing & Opt-In Live Smoke Tests**:
   - `python -m pytest`: Default execution runs 100% offline unit/integration tests without requiring network access or `GROQ_API_KEY`.
   - `python -m pytest tests/live -m live -o addopts="" -v`: Explicit command to run opt-in live API smoke tests against real Groq endpoints.
   - Live tests are excluded by default because external APIs introduce network dependency, rate limits, secret requirements, and non-deterministic execution into CI suites.

2. **Safe Error Wrapping vs Exception Chaining**:
   - Outer `RuntimeError` contains a static, safe error message (`"Groq API generation request failed."`), excluding raw provider/connection error details that might leak tokens or network topologies.
   - Exception cause (`__cause__`) preserves the full underlying exception for debugging.

3. **Provider Operational Failure != Unsupported Business Answer**:
   - **Infrastructure Operational Failure** (e.g. Groq HTTP 500 or rate limit) raises an exception that halts execution or triggers operational retries.
   - **Grounding Business Refusal** (`AnswerStatus.UNSUPPORTED`) occurs when evidence is insufficient or ungrounded, evaluated downstream by `HallucinationChecker`.
   - Infrastructure downtime must NEVER be converted to `AnswerStatus.UNSUPPORTED`.

---

## Apply the Pattern Yourself

After completing the reference tutorial, use the [Pattern 01 Learner Assignment](../assignment/ASSIGNMENT.md) to apply **Corrective RAG** independently to a different enterprise technical-support problem.

The assignment intentionally provides only the problem, constraints, and expected learning outcome. Architecture-level learners are expected to make and justify their own implementation, workflow, technology, and evaluation decisions rather than reproduce the Kubernetes reference solution.
