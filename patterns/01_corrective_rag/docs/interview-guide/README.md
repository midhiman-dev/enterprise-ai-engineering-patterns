# Use Case 01 — Interview Guide

> **Current Status:** 🟢 **Pass-15 Implemented.** Grounded interview material added for frozen Kubernetes v1.31 KB snapshot, hash integrity validation, reproducible ingestion, intentional staleness for CRAG testing, and production KB evolution.

## Overview

This guide prepares AI engineers and system designers to discuss Corrective RAG (CRAG) architecture, trade-offs, failure modes, auditability, and production scaling in technical interviews.

---

## Pass-15 — Evidence Status & Frozen Knowledge Base

### System Evidence Status Summary

| Capability / Feature | Status | Notes |
| :--- | :--- | :--- |
| **Frozen Real Kubernetes v1.31 Corpus** | Implemented + Tested | 35 curated documents from `kubernetes/website` (`snapshot-initial-v1.31`) |
| **Snapshot Integrity & Hash Validation** | Implemented + Tested | `manifest.json` SHA-256 validation via `fetch_kubernetes_snapshot.py --verify-only` |
| **Reproducible Ingestion Script** | Implemented + Tested | `scripts/fetch_kubernetes_snapshot.py` and `scripts/build_kb_index.py` |
| **FastAPI HTTP Interface** | Implemented + Tested | `create_api()`, `POST /questions`, `GET /health` |
| **SQLite DecisionTrace Persistence** | Implemented + Tested | `SQLiteDecisionTraceRepository` persistent storage |
| **Corrective Retrieval Evaluation (Golden Queries)** | Implemented + Tested | Live golden scenario evaluation harness (`evaluate_golden_scenarios.py --live`) |
| **100k-Document Scaling** | Design-only | Not implemented |
| **Incremental CDC Indexing** | Design-only | Not implemented |
| **Hybrid Lexical Retrieval (BM25 + Vector)** | Design-only | Not implemented |

---

## Pass-16 — System Evaluation & Testing Beyond Unit Tests

### Q1: "How do you test a RAG system beyond unit tests?"
**Answer:**
Testing enterprise RAG systems requires a progressive multi-layer testing strategy:

```text
Unit & Contract Tests (Mocks/Fakes)
        ↓
Retriever & Persistence Integration Tests (Local DBs)
        ↓
Provider Integration Smoke Tests (Live External APIs)
        ↓
Golden Query Behavioral Evaluation (Assembled System)
        ↓
Larger Offline Evaluation Datasets & Production Telemetry (Design-Only)
```

1. **Unit & State Machine Tests**: Fast, offline tests using handwritten fakes to verify state schema transitions, node handlers, and conditional graph routing without external network calls.
2. **Infrastructure Integration Tests**: Testing local vector store retrieval (`ChromaRetriever`) and trace persistence (`SQLiteDecisionTraceRepository`) against real local databases.
3. **Live Provider Smoke Tests**: Opt-in live tests (`pytest -m live`) verifying real third-party API credentials, wire protocol parsing, and SDK connection status (e.g. Groq, Tavily).
4. **Golden Scenario Behavioral Evaluation**: Non-invasive end-to-end execution harness (`evaluate_golden_scenarios.py --live`) running the assembled application (`build_application() -> run()`) against curated query scenarios (local known, stale version-specific, fictional premise) to record observed trace steps, web fallback usage, and answer grounding.

### Q2: "What key lesson did Pass-15B teach about mocking LLM providers in tests?"
**Answer:**
A mocked unit test validates caller logic and parameters, but it **cannot prove that a third-party hosted LLM model still exists on the provider's platform**.
During Pass-15B, unit tests with mocked Groq clients passed 100%, but live integration tests failed because the configured Groq model ID had been retired by the vendor.
**Lesson**: Mocked unit tests prove contract compliance; opt-in live integration smoke tests prove operational provider reality.

### Q3: "What is the difference between system evaluation and unit testing?"
**Answer:**
- **Unit Testing**: Verifies deterministic, binary code correctness (e.g., "does the routing function return `rewrite_query` when documents list is empty?").
- **System Evaluation**: Observes non-deterministic probabilistic system behavior (e.g., "does the relevance grader LLM recognize that a Kubernetes v1.31 document is insufficient for a v1.32 specific feature query?"). Evaluation evidence is observational rather than route-forcing.

---


## Pass-13 — Decision Trace Persistence & Auditability

### Q1: "How would you make an AI/RAG workflow auditable in an enterprise system?"
**Answer:**
Making an AI workflow auditable requires capturing explicit workflow state transitions, decision routing outcomes, and evidence provenance rather than relying on unstructured text logs.
In our CRAG architecture:
1. **Explicit Audit Entity**: An in-memory `DecisionTrace` domain entity records each executed graph node (`retrieve`, `grade_documents`, `rewrite_query`, `web_search`, `generate`, `hallucination_check`, `safe_refusal`) with explicit sequence ordering and timestamps.
2. **Domain Port Isolation**: Persistence is defined behind an abstract `DecisionTraceRepository` Domain port (`save(trace)`), isolating persistence technology choices from domain orchestration.
3. **Atomic Persistence**: Upon workflow completion, the entire trace and its ordered steps are persisted atomically in a single database transaction.

### Q2: "Why isn't standard application logging sufficient for AI decision auditing?"
**Answer:**
Standard application logs are unstructured operational diagnostic events (e.g. HTTP status, connection timeouts, exception stack traces). They are difficult to query for business/AI decision history.
An **AI DecisionTrace** is a structured, semantic execution record that answers business audit questions:
- *Why did the system execute web search?* (Because local document grading found zero relevant evidence).
- *Why did the system regenerate an answer?* (Because grounding verification failed on the first candidate answer).
- *Why did the system trigger safe refusal?* (Because grounding verification failed and candidate generation attempts exceeded `MAX_GENERATION_ATTEMPTS=2`).

### Q3: "Would you store LLM model chain-of-thought (CoT) in your audit trail?"
**Answer:**
**No.** We explicitly distinguish between **AI decision traces** and **model chain-of-thought**:
- **Decision Trace**: Stores system-verified, deterministic execution events, inputs/outputs, evidence references, and routing outcomes recorded by application code.
- **Model Chain-of-Thought**: Hidden, unverified internal reasoning steps generated by an LLM (e.g. `<think>` blocks). CoT can contain ungrounded reasoning, prompt injection leaks, or non-deterministic text. Audit trails must rely on application-recorded system decisions rather than hidden model prose.

### Q4: "Is SQLite suitable for persisting decision traces in production?"
**Answer:**
For local development, single-instance deployments, or offline tutorial execution, SQLite is ideal because it provides zero-infrastructure ACID storage with standard Python support.
At enterprise production scale with horizontally scaled microservices:
- The Domain port (`DecisionTraceRepository`) remains unchanged.
- The SQLite adapter is swapped for a `PostgresDecisionTraceRepository` or an asynchronous audit pipeline (e.g. Kafka event streaming to an analytical store).
- Storage evolves without modifying graph nodes or domain logic.

### Q5: "How should an API boundary handle malformed terminal state returned by an AI application?"
**Answer:**
The API boundary must strictly validate terminal application state against the expected application contract. If required keys (`answer`, `is_supported`, `generation_attempts`, `trace`) are missing or contain malformed types, the API returns **HTTP 500 Internal Server Error**. The API boundary must never manufacture fallback domain entities (such as fake refusal text) to repair broken runtime state, as doing so masks application invariant violations and conflates explicit domain refusals with internal system defects.
