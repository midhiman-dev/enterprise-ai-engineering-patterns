# Use Case 01 — Corrective RAG for Kubernetes Troubleshooting

> **Current Status:** 🚧 **Pass-0 — Scaffolding Only.** Architectural boundaries, package layout, and documentation templates established. No runtime AI workflow, models, or vector stores are implemented in this pass.

---

## Overview

This use case demonstrates how to engineer a **Corrective RAG (CRAG)** system using **LangGraph** within a **Clean Architecture / Ports & Adapters** framework to troubleshoot Kubernetes cluster issues.

The core learning objective is to build an agentic RAG system that evaluates its own retrieval quality, rewrites queries, falls back to web search when local knowledge is insufficient or stale, checks generated answers for hallucinations, and maintains explicit decision traces.

---

## The Problem: Deliberately Stale Knowledge Snapshot

In realistic enterprise environments, internal knowledge bases (e.g., local vector DBs) are often snapshot copies of vendor documentation that become stale over time.

This pattern simulates that exact challenge:
* **Knowledge Corpus:** 30–40 official Kubernetes troubleshooting documents frozen as a snapshot.
* **Failure Condition:** Questions about newer Kubernetes features (or absent topics) cannot be reliably answered from local retrieval alone.
* **CRAG Mitigation:** The workflow detects inadequate local retrieval, dynamically queries live web search (e.g., Tavily), and grounds answers against combined evidence.

---

## Three Golden Test Queries

The graph will be evaluated against three deterministic golden acceptance scenarios:

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
API (FastAPI DTOs & Endpoints)
  ↓
Application (AnswerQuestionUseCase & LangGraph Orchestration)
  ↓
Domain (Pure Python Entities & Ports)
  ↑
Infrastructure (Chroma, OpenAI, Tavily, Persistence Adapters)
```

* **Domain**: Pure Python entities (Question, Evidence, DecisionTrace) and ports (`Retriever`, `RelevanceGrader`, `Generator`, `WebSearchProvider`, `HallucinationChecker`). Zero third-party SDK dependencies.
* **Application**: Houses the LangGraph workflow. Graph nodes invoke Domain ports.
* **Infrastructure**: Implements Domain ports using concrete vendor SDKs.

---

## Intended Technology Stack (Future Passes)

* **Orchestration:** LangGraph / LangChain
* **Vector Store:** Chroma
* **LLM Provider:** OpenAI / Ollama
* **Web Search:** Tavily
* **API:** FastAPI
* **UI:** React

---

## Documentation & Learning Resources

* [Architecture Documentation](docs/architecture/README.md)
* [Architectural Decision Records (ADRs)](docs/adrs/README.md)
  * [ADR-001: Clean Architecture and LangGraph Boundary](docs/adrs/ADR-001-clean-architecture-and-langgraph-boundary.md)
* [Step-by-Step Tutorial (Placeholder)](docs/tutorial/README.md)
* [Interview Guide (Placeholder)](docs/interview-guide/README.md)
