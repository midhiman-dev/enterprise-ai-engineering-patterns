# Use Case 01 — Step-by-Step Tutorial

> **Current Status:** Placeholder. This tutorial will be written incrementally after the corresponding source code is implemented and verified.

## Overview

This tutorial will walk learners through building Use Case 01 (Corrective RAG for Kubernetes Troubleshooting) step by step.

In accordance with repository guidelines:
* All tutorial code snippets will be taken directly from, or accurately synchronized with, verified repository code.
* No simplified pseudo-code that materially differs from the verified solution will be introduced.

## Planned Learning & Build Sequence

The tutorial follows a deliberate learning sequence designed to isolate framework orchestration mechanics from third-party API integration complexity:

1. **Problem & Core Concepts** — The stale Kubernetes knowledge base failure mode.
2. **Domain Entities** — `Question`, `Document`, `GradedDocument`, `Answer`, `DecisionTrace`.
3. **Domain Ports** — Abstract interfaces for retrieval, grading, generation, search, and trace persistence.
4. **LangGraph State & Workflow** — Defining graph state schema, node handlers, conditional edge routing, and retry bounds.
5. **Fake / Stub Port Implementations** — Controlled in-memory stubs for testing workflow routing without external network calls.
6. **Routing & Workflow Unit Tests** — Testing all graph execution paths deterministically using port mocks.
7. **Chroma Retrieval Adapter** — Concrete vector store implementation of the `Retriever` port.
8. **OpenAI / Ollama AI Adapters** — Concrete LLM implementations of `Generator`, `RelevanceGrader`, and `HallucinationChecker`.
9. **Tavily Web Search Adapter** — Concrete implementation of `WebSearchProvider`.
10. **Decision Trace Persistence** — SQLite storage implementation of `DecisionTraceRepository`.
11. **Composition Root** — Assembling graph orchestration with concrete adapters.
12. **FastAPI / Interface** — Exposing HTTP/SSE endpoints for query processing and decision trace inspection.
13. **Integration & Golden Acceptance Tests** — Running golden queries against full adapter stack.
14. **Decision Trace Inspection** — Auditing system decisions across local vs. web fallback routes.
15. **Production Evolution & Interview Lessons** — System design trade-offs and scaling strategies.

> **Pedagogical Rationale:** Learners should first understand workflow orchestration independently of external APIs. LangGraph routing must be executable and testable using controlled fake implementations before introducing provider integration complexity.
