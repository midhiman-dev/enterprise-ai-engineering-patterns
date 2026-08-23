# Use Case 01 — Corrective RAG for Kubernetes Troubleshooting

> **Current Status:** 🟢 **Pass-15 — Frozen Kubernetes v1.31 Knowledge Base Implemented.** Frozen Kubernetes v1.31 Knowledge Base snapshot (35 curated documents from `kubernetes/website` tag `snapshot-initial-v1.31`, commit `20d164c7a7d092ebc65eed06c855d2ec4f0f0e12`), provenance manifest (`manifest.json`), CC BY 4.0 attribution (`ATTRIBUTION.md`), snapshot reproduction script (`scripts/fetch_kubernetes_snapshot.py`), offline snapshot integrity tests (`tests/snapshot/`), ADR-011, and tutorial/interview updates are complete and verified.


---

## Overview

This use case demonstrates how to engineer a **Corrective RAG (CRAG)** system using **LangGraph** within a **Clean Architecture / Ports & Adapters** framework to troubleshoot Kubernetes cluster issues.

The core learning objective is to build a self-correcting RAG workflow orchestrated with LangGraph that evaluates its own retrieval quality, rewrites queries, falls back to web search when local knowledge is insufficient or stale, checks generated answers for hallucinations, and maintains explicit decision traces.

> **Note on Framework Terminology:** LangGraph can orchestrate deterministic workflows, stateful AI workflows, and agentic systems. Using LangGraph does not automatically make an application an agent. This pattern demonstrates a stateful, conditional workflow with explicit graph state, routing logic, and bounded retries.

---

## The Problem: Deliberately Stale Knowledge Snapshot

In realistic enterprise environments, internal knowledge bases (e.g., local vector DBs) are often snapshot copies of vendor documentation that become stale over time.

This pattern simulates that exact challenge:
* **Knowledge Corpus:** 30–40 official Kubernetes troubleshooting documents frozen as a snapshot.
* **Failure Condition:** Questions about newer Kubernetes features (or absent topics) cannot be reliably answered from local retrieval alone.
* **CRAG Mitigation:** The workflow detects inadequate local retrieval, dynamically queries live web search (e.g. Tavily), and grounds answers against combined evidence.

---

## Three Golden Test Queries

The graph will be evaluated against three golden acceptance scenarios with expected graph routes:

> Controlled unit and acceptance tests using stub ports make graph routing deterministic, whereas live provider execution remains probabilistic.

1. **Local Knowledge Sufficient:**
   * *Query:* `Why does kubectl get pods show CrashLoopBackOff?`
   * *Route:* `retrieve` -> `grade_documents` -> `generate` -> `hallucination_check` -> `answer`
2. **Local Knowledge Stale / Insufficient:**
   * *Query:* `How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?`
   * *Route:* `retrieve` -> `grade_documents` -> `rewrite_query` -> `web_search` -> `generate` -> `hallucination_check` -> `answer`
3. **Fabricated Premise (Refusal / Safety):**
   * *Query:* `What does the --enable-quantum-scheduler flag do in kubectl?`
   * *Route:* `retrieve` / `web_search` -> `generate` -> `hallucination_check` -> `retry or safe refusal`

---

## High-Level Architecture & Layer Boundaries

```text
UI (React / TypeScript)
  ↓
API (FastAPI DTOs & Endpoints in src/corrective_rag/api/)
  ↓
Application (CorrectiveRAGApplication & LangGraph Orchestration)
  ↓
Domain (Pure Python Entities & Ports)
  ↑
Infrastructure (Chroma, Groq, Tavily, SQLite Persistence Adapters)
```

* **Domain**: Pure Python entities (`Question`, `Document`, `GradedDocument`, `Answer`, `DecisionTrace`) and ports (`Retriever`, `RelevanceGrader`, `QueryRewriter`, `Generator`, `WebSearchProvider`, `HallucinationChecker`, `DecisionTraceRepository`). Zero third-party SDK dependencies.
* **Application**: Houses the LangGraph workflow (`CorrectiveRAGApplication`). Graph nodes invoke Domain ports.
* **Infrastructure**: Implements Domain ports using concrete vendor SDKs.
* **Composition**: Assembles concrete Infrastructure adapters into `WorkflowDependencies` and compiles `CorrectiveRAGApplication`.
* **API**: Exposes HTTP endpoints (`create_api()`) delegating to `CorrectiveRAGApplication.run(question)`.

---

## HTTP API Endpoints

### 1. Process Liveness Health Check
* **Method & Path:** `GET /health`
* **Response:** `{"status": "ok"}`
* **Behavior:** Process-level liveness probe. Does not execute downstream database, vector, or LLM queries.

### 2. Submit Troubleshooting Question
* **Method & Path:** `POST /questions`
* **Request JSON:**
  ```json
  {
    "question": "Why does kubectl get pods show CrashLoopBackOff?"
  }
  ```
* **Response JSON:**
  ```json
  {
    "answer": "...",
    "status": "answered",
    "is_supported": true,
    "generation_attempts": 1,
    "decision_trace": [
      { "step": "retrieve", "detail": null },
      { "step": "grade_documents", "detail": null },
      { "step": "generate", "detail": null },
      { "step": "hallucination_check", "detail": null }
    ]
  }
  ```

### Minimal Local Execution
To launch the FastAPI development server locally:
```bash
python -m uvicorn corrective_rag.api.app:create_api --factory --reload
```

---

## Documentation & Learning Resources

* [Architecture Documentation](docs/architecture/README.md)
* [Architectural Decision Records (ADRs)](docs/adrs/README.md)
  * [ADR-001: Clean Architecture and LangGraph Boundary](docs/adrs/ADR-001-clean-architecture-and-langgraph-boundary.md)
  * [ADR-002: Local Vector Retrieval with Chroma](docs/adrs/ADR-002-local-vector-retrieval-with-chroma.md)
  * [ADR-003: Groq as the Initial Hosted Generation Provider](docs/adrs/ADR-003-groq-hosted-generation-adapter.md)
  * [ADR-004: LLM Relevance Grading with Validated JSON Output](docs/adrs/ADR-004-llm-relevance-grading-with-structured-output.md)
  * [ADR-005: LLM Query Rewriting for Corrective Retrieval](docs/adrs/ADR-005-llm-query-rewriting-for-corrective-retrieval.md)
  * [ADR-006: Tavily Web Search for Corrective Retrieval](docs/adrs/ADR-006-tavily-web-search-for-corrective-retrieval.md)
  * [ADR-007: Evidence Grounding Verification for Generated Answers](docs/adrs/ADR-007-evidence-grounding-verification.md)
  * [ADR-008: Composition Root and Real Adapter Runtime Wiring](docs/adrs/ADR-008-composition-root-and-runtime-wiring.md)
  * [ADR-009: SQLite Persistence for DecisionTrace Audit Records](docs/adrs/ADR-009-sqlite-decision-trace-persistence.md)
  * [ADR-010: FastAPI HTTP Interface Boundary](docs/adrs/ADR-010-fastapi-http-interface.md)


* [Step-by-Step Tutorial](docs/tutorial/README.md)
* [Interview Guide](docs/interview-guide/README.md)
