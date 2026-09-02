# Use Case 01 — Corrective RAG for Kubernetes Troubleshooting

> **Current Status:** 🟢 **Pass-16 — External Evidence Trust Boundary Implemented.** Frozen Kubernetes v1.31 knowledge snapshot, provenance manifest, corrective web search, authoritative external-source allowlisting, explicit external-evidence trust metadata, instruction/data separation for retrieved evidence, indirect prompt-injection boundary tests, ADR-012, and a dedicated tutorial lesson are implemented.

---

## Overview

This use case demonstrates how to engineer a **Corrective RAG (CRAG)** system using **LangGraph** within a **Clean Architecture / Ports & Adapters** framework to troubleshoot Kubernetes cluster issues.

The core learning objective is to build a self-correcting RAG workflow orchestrated with LangGraph that evaluates its own retrieval quality, rewrites queries, falls back to controlled web search when local knowledge is insufficient or stale, checks generated answers for hallucinations, preserves explicit decision traces, and treats external evidence as a first-class security trust boundary.

> **Note on Framework Terminology:** LangGraph can orchestrate deterministic workflows, stateful AI workflows, and agentic systems. Using LangGraph does not automatically make an application an agent. This pattern demonstrates a stateful, conditional workflow with explicit graph state, routing logic, and bounded retries.

---

## The Problem: Deliberately Stale Knowledge Snapshot

In realistic enterprise environments, internal knowledge bases (e.g., local vector DBs) are often snapshot copies of vendor documentation that become stale over time.

This pattern simulates that exact challenge:
* **Knowledge Corpus:** 30–40 official Kubernetes troubleshooting documents frozen as a snapshot.
* **Failure Condition:** Questions about newer Kubernetes features (or absent topics) cannot be reliably answered from local retrieval alone.
* **CRAG Mitigation:** The workflow detects inadequate local retrieval, dynamically queries controlled live web search (Tavily), and grounds answers against combined evidence.
* **Security Consequence:** External search introduces content controlled outside the application into the LLM context, creating an **indirect prompt-injection trust boundary**.

---

## External Evidence Trust Boundary

Corrective retrieval improves freshness but expands the attack surface:

```text
controlled local corpus
        ↓ stale / insufficient
query rewrite
        ↓
Tavily web search
        ↓
external content
        ↓
authoritative-source allowlist
        ↓
provenance + trust metadata
        ↓
REFERENCE DATA boundary
        ↓
LLM generation
        ↓
grounding verification
```

Implemented controls:

1. **Authoritative HTTPS source allowlist** — external results are admitted only when their URL matches configured source prefixes.
2. **Explicit provenance** — accepted external `Document` objects carry `retrieval_channel`, `source_trust`, and `source_policy` metadata.
3. **Instruction/data separation** — retrieved content stays in evidence/user-message blocks and is never promoted to the system-message role.
4. **Prompt-level authority rule** — the generator explicitly states that retrieved evidence is reference data and cannot override system rules, request secrets, authorize actions, or change tool behavior.
5. **Grounding verification remains active** — the security boundary complements rather than replaces evidence-grounding checks.

> **Important:** This pattern does **not** claim that prompt injection is solved. Source allowlisting and prompt separation reduce risk, but allowlisted content can still be compromised or adversarial and LLM behavior remains probabilistic.

Architectural principle:

> **Source authority is not instruction authority. Retrieved content may provide evidence, but it must never silently acquire control authority.**

Configuration:

```ini
TAVILY_ALLOWED_SOURCE_PREFIXES=https://kubernetes.io/,https://github.com/kubernetes/
```

See:

* [ADR-012: External Evidence Trust Boundary and Indirect Prompt-Injection Controls](docs/adrs/ADR-012-external-evidence-trust-boundary-and-indirect-prompt-injection.md)
* [Tutorial Lesson 21: External Evidence Trust Boundary and Indirect Prompt Injection](docs/tutorial/21-external-evidence-trust-boundary-and-indirect-prompt-injection.md)

---

## Three Golden Test Queries

The graph is evaluated against three golden acceptance scenarios with expected graph routes:

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
* **Infrastructure**: Implements Domain ports using concrete vendor SDKs and enforces provider-boundary controls such as the Tavily external-source policy.
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

---

## Developer Local Environment Setup

Copy `.env.example` to create your developer-local `.env` file:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# Linux / macOS bash
cp .env.example .env
```

Configure your credentials and external-source policy inside `.env`:
```ini
GROQ_API_KEY=your_real_groq_api_key
TAVILY_API_KEY=your_real_tavily_api_key
TAVILY_ALLOWED_SOURCE_PREFIXES=https://kubernetes.io/,https://github.com/kubernetes/
```

> **Note:** `.env` is ignored by Git and will never be committed. Deployment and process environment variables always take precedence over `.env` settings (`override=False`).

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
  * [ADR-011: Frozen Kubernetes v1.31 Knowledge Snapshot for Corrective RAG](docs/adrs/ADR-011-frozen-kubernetes-knowledge-snapshot.md)
  * [ADR-012: External Evidence Trust Boundary and Indirect Prompt-Injection Controls](docs/adrs/ADR-012-external-evidence-trust-boundary-and-indirect-prompt-injection.md)
* [Step-by-Step Tutorial](docs/tutorial/README.md)
* [Tutorial Lesson 21 — External Evidence Trust Boundary and Indirect Prompt Injection](docs/tutorial/21-external-evidence-trust-boundary-and-indirect-prompt-injection.md)
* [Interview Guide](docs/interview-guide/README.md)
