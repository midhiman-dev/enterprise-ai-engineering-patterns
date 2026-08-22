# Use Case 01 — Step-by-Step Tutorial

> **Current Status:** 🟢 **Pass-10 Implemented.** Tavily web search infrastructure adapter (`TavilyWebSearchProvider`), config loader (`TavilyConfig`), client abstraction (`TavilySearchClient`), offline unit tests with handwritten fake client, opt-in live smoke test (`test_tavily_web_search_live.py`), and ADR-006 are complete and verified.


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
11. **Groq Relevance Grader** — Concrete implementation of `RelevanceGrader` (`GroqRelevanceGrader`). (Implemented)
12. **Groq Query Rewriter** — Concrete implementation of `QueryRewriter` (`GroqQueryRewriter`). (Implemented)
13. **Tavily Web Search Adapter** — Concrete implementation of `WebSearchProvider` (`TavilyWebSearchProvider`). (Implemented)

14. **Groq Hallucination Checker** — Concrete implementation of `HallucinationChecker`.
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

## Pass-8 Learning Outline — Groq Relevance Grader with Validated JSON Output

Pass-8 demonstrates how document relevance grading is implemented behind the Domain `RelevanceGrader` port using Groq prompt-constrained JSON and strict application-side validation:

```text
query
  ↓
Chroma top-k candidates
  ↓
one candidate
  ↓
GroqRelevanceGrader
  ↓
GradedDocument
```

### Three Levels of Output Contracts

```text
Level 1 — Free-form output
"Yes, this document seems relevant because..."
          ↓
    fragile prose parsing


Level 2 — Prompt-constrained JSON [CURRENT IMPLEMENTATION]
Prompt:
  Return only:
  {"is_relevant": true|false, "reason": "..."}
          ↓
     model text
          ↓
    json.loads()
          ↓
   strict validation


Level 3 — Provider-native structured output [DESIGN-ONLY]
JSON Schema / response_format
          ↓
   provider-constrained generation
          ↓
   application validation
```

### Key Technical Concepts & Learner Takeaways

1. **Vector Distance $\neq$ Relevance Decision**:
   - Chroma vector retrieval optimizes candidate recall using embedding similarity distance.
   - Vector distance measures mathematical proximity, not task-specific evidence utility. A document can be vector-near while still failing to answer the user's prompt.
   - `RelevanceGrader` performs semantic evidence validation on candidate documents after retrieval.

2. **Prompt-Constrained JSON with Strict Application-Side Validation**:
   - Prompts Groq for JSON-formatted text: `{"is_relevant": true|false, "reason": "..."}`.
   - Strict standard-library validation (`parse_relevance_result`) enforces exact key constraints (`{"is_relevant", "reason"}`), boolean type checking (`type(val) is bool`), and non-blank string rationales.
   - Avoids fragile substring matching (e.g. searching for "yes" or "true" in raw prose) without requiring vendor-specific SDK schema enforcement in the client protocol.

3. **Probabilistic Judgment vs. Deterministic Validation**:
   - The LLM relevance judgment itself remains **probabilistic**.
   - What becomes **deterministic** is JSON parsing, type validation, and downstream graph routing once a valid result exists.

4. **Explicit Score Semantics (`score=None`)**:
   - `GradedDocument` is instantiated with `score=None`.
   - Numeric confidence values (0.0–1.0) are omitted until explicitly calibrated domain score semantics are defined.

5. **Operational Failure Isolation**:
   - Malformed provider outputs or API failures raise `RuntimeError`.
   - Operational provider errors are NEVER silently converted into `is_relevant=False` decisions.

---

## Interview Guide — Why Not Just Use Similarity Score for Document Relevance?

> **Interview Question:** Why does CRAG introduce a downstream LLM Relevance Grader instead of relying on Chroma's similarity score distance threshold?

### Answer Strategy

1. **Embedding Proximity vs Semantic Utility**: Vector distance measures high-level topic proximity in embedding space. In complex technical domains, a document often shares broad keywords (e.g. general Kubernetes cluster management) but lacks the specific diagnostic steps or causes required for the prompt.
2. **Threshold Calibration Instability**: Similarity score distributions vary dramatically across embedding models, vector index configurations, chunking boundaries, and domain query structures. Setting a fixed distance threshold causes high false-positive or false-negative rates.
3. **Task-Specific Evidence Judgment**: Downstream LLM grading evaluates the candidate document specifically against the user's question, producing an explicit decision (`is_relevant`) alongside a human-auditable rationale (`reason`).

---

## Pass-9 Learning Outline — Groq Query Rewriter Infrastructure Adapter

Pass-9 demonstrates how query rewriting is implemented behind the Domain `QueryRewriter` port using the Groq hosted LLM provider.

```text
Domain Question (Original Intent)
       │
       ├───────────────────────────────┐
       ▼                               ▼
Relevance Grading              GroqQueryRewriter
                                       │
                                       ▼
                             rewritten search query
                                       │
                                       ▼
                                  Web Search
                                       │
                                       ▼
                                   evidence
                                       │
                                       ▼
                                   Generator
                                       │
                                       ▼
                          ORIGINAL Question + Evidence
```

### Domain Port Contract

```python
class QueryRewriter(Protocol):
    """Port for rewriting questions for optimized retrieval."""

    def rewrite(self, question: Question) -> Question:
        """Rewrite a question into a refined natural-language retrieval question."""
        ...
```

### Infrastructure Adapter Implementation

Excerpts from `GroqQueryRewriter` showing prompt building, execution, and blank-output validation:

```python
def build_query_rewrite_messages(question: Question) -> list[dict[str, str]]:
    user_content = (
        f"Original User Question:\n{question.text}\n\n"
        "Rewrite the above question into a concise search query for external technical documentation."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


class GroqQueryRewriter:
    """Concrete Groq implementation of the Domain QueryRewriter port."""

    def __init__(self, config: GroqConfig, client: GroqChatClient) -> None:
        self._config = config
        self._client = client

    def rewrite(self, question: Question) -> Question:
        messages = build_query_rewrite_messages(question)
        raw_response = self._client.complete(
            model=self._config.model,
            messages=messages,
            temperature=self._config.temperature,
        )

        if not raw_response or not raw_response.strip():
            raise RuntimeError("Groq returned an empty rewritten query.")

        return Question(text=raw_response.strip())
```

### Key Architectural Rules & Takeaways

1. **Query Rewriting is Retrieval Optimization, NOT Answer Generation**:
   - `question`: Represents user intent. It remains immutable and is preserved in `GraphState["question"]`.
   - `rewritten_question`: Represents retrieval search strategy. It is stored separately in `GraphState["rewritten_question"]` and used only by web search.
2. **Defensive Search Prompting**:
   - Strips conversational phrases while preserving technical entities and version numbers (e.g. `Kubernetes 1.32`).
   - Does NOT verify or answer whether fictitious premises (e.g. `--enable-quantum-scheduler`) exist.
3. **Failure Handling**:
   - Blank provider outputs raise operational `RuntimeError("Groq returned an empty rewritten query.")`.
   - Operational failures are never silently converted into the original question or a business response.

---

## Interview Guide — Why Not Replace the Original Question with the Rewritten One?

> **Interview Question:** In a Corrective RAG pipeline, why shouldn't you overwrite `state["question"]` with the LLM's rewritten query?

### Answer Strategy

1. **Retrieval Strategy vs. User Intent**: Query rewriting is a probabilistic optimization designed to increase external search engine recall. The rewritten string is optimized for search indexing, not for answering the user's intent.
2. **Risk of Query Drift**: An LLM rewriter can drop essential context, alter technical terms, or drift from the original request.
3. **Grounded Answer Generation**: The final `Generator` must produce an answer to what the user *actually asked*. Answering the rewritten search query risks giving a technically accurate answer to a different question.

---

## Pass-10 Learning Outline — Tavily Web Search Infrastructure Adapter

Pass-10 demonstrates how external corrective web search is implemented behind the Domain `WebSearchProvider` port using Tavily Search API.

```text
rewritten search query
          ↓
TavilyWebSearchProvider (TavilyConfig)
          ↓
TavilySearchClient (Infrastructure Protocol)
          ↓
TavilySdkSearchClient (Tavily SDK)
          ↓
Provider JSON Response Payload
          ↓
Normalizer (Field Extraction & Defensive Validation)
          ↓
Domain Document[] (content, source, title, source_url, metadata)
```

### Domain Port Contract

```python
class WebSearchProvider(Protocol):
    """Port for searching external web sources."""

    def search(self, question: Question) -> Sequence[Document]:
        """Search external web sources for evidence relevant to the question."""
        ...
```

### Infrastructure Adapter & Config Implementation

Excerpts from `TavilyConfig` and `TavilyWebSearchProvider` showing configuration validation and provider response normalization:

```python
@dataclass(frozen=True)
class TavilyConfig:
    api_key: str
    max_results: int = DEFAULT_TAVILY_MAX_RESULTS

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("TAVILY_API_KEY is required.")
        if self.max_results <= 0:
            raise ValueError("max_results must be greater than 0.")


class TavilyWebSearchProvider:
    def __init__(self, config: TavilyConfig, client: TavilySearchClient) -> None:
        self._config = config
        self._client = client

    def search(self, question: Question) -> Sequence[Document]:
        try:
            raw_response = self._client.search(
                query=question.text,
                max_results=self._config.max_results,
            )
        except Exception as exc:
            raise RuntimeError("Tavily search request failed.") from exc

        if not raw_response or not isinstance(raw_response, dict):
            return []

        raw_results = raw_response.get("results")
        if not raw_results or not isinstance(raw_results, list):
            return []

        documents: list[Document] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue

            raw_content = item.get("content")
            if not raw_content or not isinstance(raw_content, str) or not raw_content.strip():
                continue

            raw_url = item.get("url")
            if not raw_url or not isinstance(raw_url, str) or not raw_url.strip():
                continue

            metadata: dict[str, object] = {}
            raw_score = item.get("score")
            if isinstance(raw_score, (int, float)):
                metadata["tavily_score"] = float(raw_score)

            doc = Document(
                content=raw_content.strip(),
                source=raw_url.strip(),
                title=item.get("title").strip() if isinstance(item.get("title"), str) and item.get("title").strip() else None,
                source_url=raw_url.strip(),
                metadata=metadata,
            )
            documents.append(doc)

        return documents
```

### Key Architectural Rules & Takeaways

1. **Provider Isolation**:
   - `question.text` is forwarded directly as the query string without modifying the original question object.
   - Tavily-specific response dictionaries and scores (`score`) are mapped to provider-neutral `Document` entities inside the Infrastructure layer.
2. **Search Engine Ranking Score $\neq$ Downstream Relevance Grade**:
   - Tavily result scores (`score`) are provider-returned result scores.
   - Downstream `RelevanceGrader` and `Generator` nodes remain authoritative for evaluating semantic relevance and evidence grounding. Tavily scores are preserved strictly in `Document.metadata["tavily_score"]`.
3. **Failure Differentiation**:
   - Empty search results (`{"results": []}`) return an empty list `[]` cleanly.
   - Operational API failures raise `RuntimeError("Tavily search request failed.")` chained with `from exc`.

---

## Interview Guide — How Does Web Search Handling Differ from Local Vector Storage?

> **Interview Question:** What are the key architectural differences between local vector retrieval and external web search in a CRAG pipeline?

### Answer Strategy

1. **Trust & Data Hygiene**: Local vector storage operates over curated, internal enterprise documentation. External web search retrieves untrusted external web content requiring strict isolation to prevent indirect prompt injection and data leakage.
2. **Privacy Policy Checks**: Before invoking external search APIs, production systems require PII detection and allowlist filtering to prevent accidental leakage of sensitive internal terms or infrastructure names.
3. **Score Semantics**: Vector similarity distance measures embedding-space proximity, whereas a Tavily result score is provider-defined retrieval metadata. Neither score replaces explicit LLM relevance grading and hallucination verification.

---

## Apply the Pattern Yourself

After completing the reference tutorial, use the [Pattern 01 Learner Assignment](../assignment/ASSIGNMENT.md) to apply **Corrective RAG** independently to a different enterprise technical-support problem.

The assignment intentionally provides only the problem, constraints, and expected learning outcome. Architecture-level learners are expected to make and justify their own implementation, workflow, technology, and evaluation decisions rather than reproduce the Kubernetes reference solution.
