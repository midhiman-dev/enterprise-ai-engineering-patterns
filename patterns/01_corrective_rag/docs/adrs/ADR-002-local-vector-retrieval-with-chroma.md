# ADR-002: Local Vector Retrieval with Chroma

## Status
**Accepted**

## Date
2026-08-21

## Context

The Corrective RAG (CRAG) system requires candidate document retrieval from a local knowledge base.

To fulfill the repository's educational objectives, the retrieval component must demonstrate real vector search semantics—loading source documents, chunking text, generating numeric embeddings, indexing into a vector database, querying top-k candidates, and converting vendor results into provider-neutral Domain entities.

Key constraints for this architectural slice:
1. **Zero External Infrastructure**: Learners must be able to run retrieval locally without provisioning external database servers or cloud vector services.
2. **Framework & Adapter Transparency**: Learners should inspect raw vector store operations (indexing, querying, top-k selection, metadata handling) rather than hiding them behind framework abstractions.
3. **Clean Architecture Boundary Isolation**: The `Domain` and `Application` layers must remain 100% pure Python without vendor SDK imports (`chromadb`, `Chroma`).
4. **Offline Testability**: Integration tests must execute offline without requiring cloud API keys or downloading heavy external model weights at test execution time.

## Decision

We decide to:
1. Implement the local vector database retrieval capability using **Chroma** directly via its native Python API (`chromadb`).
2. Create `ChromaRetriever` inside `src/corrective_rag/infrastructure/retrieval/chroma_retriever.py`, which structurally satisfies the Domain `Retriever` protocol interface (`def retrieve(self, question: Question) -> Sequence[Document]`) without explicit inheritance.
3. Isolate all document loader (`DocumentLoader`), chunking (`DocumentChunker`), indexing (`ChromaIndexer`), and embedding logic inside the `Infrastructure` layer.
4. Provide a deterministic offline embedding function (`DeterministicTestEmbeddingFunction`) for fast integration testing without network calls or external downloads.
5. Store persistent local vector database files under a gitignored workspace path (`data/chroma/`).

## Alternatives Considered

### 1. FAISS (Facebook AI Similarity Search)
* **Pros**: Extremely fast in-memory similarity search.
* **Cons**: Operates strictly on raw arrays without built-in document metadata management or persistent collection semantics. Requires manual mapping for document content and provenance metadata.

### 2. PostgreSQL + `pgvector`
* **Pros**: Standard enterprise pattern for relational + vector workloads.
* **Cons**: Requires running a local PostgreSQL container or service, violating the zero-external-infrastructure requirement for quick learner onboarding.

### 3. Managed Vector Databases (Pinecone, Qdrant Cloud, Azure AI Search)
* **Pros**: Realistic production scale and cloud features.
* **Cons**: Requires active cloud accounts, API keys, network access, and cost management, preventing zero-setup offline execution.

### 4. LangChain VectorStore Abstraction (`langchain-chroma`, `langchain-community`)
* **Pros**: Higher-level helper functions for chunking and embedding.
* **Cons**: Conceals vector store operations behind mini-framework abstractions, violating Rule 2 (Framework Visibility).

## Consequences

### Positive
* **Zero Infrastructure Overhead**: Runs embedded in Python out of the box using local persistent disk storage.
* **Pedagogical Clarity**: Learners explicitly trace chunking, embedding, indexing, querying, and Domain mapping.
* **Clean Architecture Isolation**: The Domain and Application layers know nothing about Chroma, enabling seamless future adapter swaps.
* **Fast Offline Testing**: Integration tests run in under 2 seconds without external dependencies.

### Trade-offs
* Local filesystem storage differs from distributed enterprise production vector databases.
* Single-node Chroma persistence is not intended for multi-tenant high-throughput scaling.

## Interview Takeaway

> **Why Clean Architecture Isolates Vector Databases**:
> Application orchestration depends strictly on the Domain `Retriever` port contract (`retrieve(Question) -> Sequence[Document]`).
> Whether candidate documents originate from local Chroma, PostgreSQL with `pgvector`, Pinecone, or Azure AI Search, the core state graph and routing logic remain unchanged.
> While swapping database vendors in production involves operational data migration and re-indexing, Application-layer code requires zero modifications.

## Diagnostic Sequence: Retrieval Failure vs. Generation Failure

> **A RAG system can hallucinate even when the correct answer exists in the corpus if retrieval fails to surface the right evidence.**

When investigating a RAG system failure, follow this diagnostic sequence before assuming LLM hallucination:

1. **Indexing Verification**: Is the source document actually ingested in the collection?
2. **Chunking Boundary Check**: Was the relevant text split across chunk boundaries or truncated?
3. **Embedding Representation**: Did the query embedding capture the semantic intent of the question?
4. **Top-K Parameter**: Was `top_k` set too small to retrieve candidates beyond surrounding noise?
5. **Metadata Filtering**: Were metadata filters incorrectly excluding valid documents?
6. **Hybrid Retrieval**: Would adding BM25 lexical keyword search improve recall for exact product terms or error codes?
7. **Reranking**: Would a cross-encoder reranker improve candidate ordering before passing evidence to the LLM?
8. **Evaluation Dataset**: Does the test dataset contain golden queries that specifically measure retrieval recall (e.g. MRR, Hit@K)?
