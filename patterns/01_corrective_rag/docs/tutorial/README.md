# Use Case 01 — Step-by-Step Tutorial

> **Current Status:** 🟢 **Pass-3 Implemented.** Domain entities, domain ports, LangGraph state (`GraphState`), straight workflow nodes (`retrieve`, `grade_documents`, `generate`, `hallucination_check`), handwritten deterministic fakes, and application unit tests are implemented and verified.


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
7. **Query Rewriting & Web Search Routing** — Adding stale-KB detection and web fallback routing branches.
8. **Chroma Retrieval Adapter** — Concrete vector store implementation of the `Retriever` port.
8. **OpenAI / Ollama AI Adapters** — Concrete LLM implementations of `Generator`, `RelevanceGrader`, and `HallucinationChecker`.
9. **Tavily Web Search Adapter** — Concrete implementation of `WebSearchProvider`.
10. **Decision Trace Persistence** — SQLite storage implementation of `DecisionTraceRepository`.
11. **Composition Root** — Assembling graph orchestration with concrete adapters.
12. **FastAPI / Interface** — Exposing HTTP/SSE endpoints for query processing and decision trace inspection.
13. **Integration & Golden Acceptance Tests** — Running golden queries against full adapter stack.
14. **Decision Trace Inspection** — Auditing system decisions across local vs. web fallback routes.
15. **Production Evolution & Interview Lessons** — System design trade-offs and scaling strategies.

> **Pedagogical Rationale:** Learners should first understand workflow orchestration independently of external APIs. LangGraph routing must be executable and testable using controlled fake implementations before introducing provider integration complexity. Handwritten fakes make workflow testing deterministic and isolate orchestration logic from network and vendor API variability.
