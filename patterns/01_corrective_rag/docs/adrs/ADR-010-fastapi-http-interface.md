# ADR-010: FastAPI HTTP Interface Boundary

* **Status:** Accepted
* **Date:** 2026-08-23
* **Deciders:** AI Engineering Team

---

## Context & Problem Statement

Through Pass-13, the Corrective RAG (CRAG) system built an executable application boundary (`CorrectiveRAGApplication`), bundling compiled LangGraph workflow orchestration with SQLite trace persistence (`DecisionTraceRepository`). 

However, until Pass-14, the application could only be executed via Python unit/integration tests or programmatic script calls. To enable local execution, HTTP API access, web client integration, and containerized service deployment, the application requires an explicit HTTP transport interface layer.

The core architectural challenge is exposing the workflow over HTTP without coupling transport concerns to domain entity logic, orchestration routing, or infrastructure providers.

---

## Decision

We introduce an explicit HTTP transport interface layer using **FastAPI** in `src/corrective_rag/api/`.

Key design points:

1. **Thin Controller Principle**: FastAPI routes delegate execution strictly to `CorrectiveRAGApplication.run(question)`. Route handlers do NOT contain retrieval, grading, generation, query rewriting, web search, grounding, or persistence logic.
2. **DTO Boundary Isolation**: HTTP transport models (`QuestionRequest`, `QuestionResponse`, `DecisionTraceStepResponse`, `HealthResponse`) are defined separately in `api/models.py`. Domain entities (`Question`, `Answer`, `DecisionTrace`) remain pure and isolated from HTTP/Pydantic serialization details.
3. **Application Factory & Lifecycle**: An explicit factory function `create_api(application: CorrectiveRAGApplication | None = None)` initializes the web application. In production, `build_application()` is called once during startup to construct the single `CorrectiveRAGApplication` instance. In tests, a test/fake application instance is injected cleanly without global monkeypatching.
4. **Synchronous Execution Route**: Route handlers use synchronous function definitions (`def ask_question(...)`) matching the synchronous application workflow and provider contracts.
5. **Inline DecisionTrace Response**: The current execution's `DecisionTrace` is returned inline in `POST /questions` responses (`decision_trace`). SQLite row primary keys are not exposed, respecting ADR-009.
6. **Liveness Health Endpoint**: `GET /health` provides process-level liveness verification without probing downstream databases or external AI service providers.

```text
HTTP Request DTO (QuestionRequest)
              ↓
    FastAPI Route (ask_question)
              ↓
  Domain Question Entity Mapping
              ↓
    CorrectiveRAGApplication.run(...)
              ↓
     LangGraph Workflow Nodes
              ↓
  SQLite DecisionTrace Persistence
              ↓
HTTP Response DTO (QuestionResponse)
```

---

## Why FastAPI?

FastAPI was selected for this transport layer because:
* **Python AI Ecosystem Alignment**: FastAPI is widely used in Python AI/ML service development.
* **Pydantic Validation**: Automatic request DTO parsing, type enforcement, and explicit error responses (HTTP 422).
* **OpenAPI Documentation**: Automatic OpenAPI/Swagger documentation generation from Pydantic DTO models and route annotations.
* **Minimal Transport Overhead**: Lightweight ASGI framework with zero forced ORM or framework magic.

---

## Alternatives Considered

### 1. CLI Only
* **Pros**: Simple script execution without web dependencies.
* **Cons**: Fails the requirement for HTTP service deployment and UI integration.

### 2. Flask
* **Pros**: Mature WSGI framework.
* **Cons**: Lacks modern type hint integration, native Pydantic schema validation, and automatic OpenAPI generation without third-party plugins.

### 3. FastAPI (Selected)
* **Pros**: Type-safe Pydantic DTO validation, automatic OpenAPI specs, lightweight transport layer.
* **Cons**: Adds `fastapi` and `uvicorn` runtime dependencies.

### 4. LangServe / Framework-Specific Serving Abstractions
* **Pros**: Turnkey API endpoints wrapping LangChain/LangGraph runnables.
* **Cons**: Hides routing mechanics and HTTP DTO mapping behind framework abstractions, violating the learner-first explicit architecture rule.

---

## Key Technical & Design Principles

### 1. Thin Controller Principle
FastAPI routes act purely as transport adapters:
* Parsing HTTP JSON payloads into transport DTOs (`QuestionRequest`).
* Mapping transport DTOs into Domain entities (`Question`).
* Delegating execution to `CorrectiveRAGApplication.run(question)`.
* Mapping application results (`GraphState`) into HTTP response DTOs (`QuestionResponse`).

Routes NEVER invoke Groq, Tavily, Chroma, SQLite, or `graph.invoke()` directly.

### 2. Domain Entities vs. HTTP Transport DTOs
* `Question`: Domain entity enforcing business rules (non-blank string, original wording preservation).
* `QuestionRequest`: HTTP DTO defining wire contract validation rules (Pydantic field validation returning HTTP 422 for invalid payloads).
* `Answer`: Domain entity tracking answer text and `AnswerStatus`.
* `QuestionResponse`: HTTP DTO decoupling wire representation from internal graph state structure.

### 3. Application Outcome (HTTP 200) vs. Operational Failure (HTTP 500)
A critical enterprise distinction:
* **Application Outcome (Safe Refusal)**: Golden Query 3 (unsupported premise / insufficient evidence) is a valid business outcome. `AnswerStatus.UNSUPPORTED` returns **HTTP 200 OK** with `status = "unsupported"` and `is_supported = false`.
* **Operational Failure**: Infrastructure outages (Groq 500, Tavily timeout, Chroma error, SQLite disk error) are operational failures. The route catches unhandled exceptions and returns a generic **HTTP 500 Internal Server Error** without leaking API keys, DB paths, prompts, or stack traces.

### 4. Process Liveness (`/health`) vs. Dependency Readiness
* `GET /health` is strictly a process-level **liveness probe** confirming the Python ASGI web process is running.
* It does NOT execute vector queries, LLM calls, or database checks, ensuring health checks remain fast, cheap, and non-disruptive.

### 5. Synchronous Route Decision
The underlying LangGraph state graph and capability adapters execute synchronously. Converting API routes to `async def` without async provider SDKs would provide false concurrency guarantees. Synchronous routes match the current application contract.

### 6. Valid Application Outcome vs. Broken Application Contract
A critical design principle enforces strict validation of the terminal application contract:
* **Valid Application Outcome**: When `application.run(question)` completes with a valid `Answer` entity (including `AnswerStatus.UNSUPPORTED`), exact boolean `is_supported`, non-negative integer `generation_attempts`, and a `DecisionTrace` entity, the API maps the outcome to **HTTP 200 OK**.
* **Broken Application Contract / Malformed State**: If terminal state is missing required keys (`answer`, `is_supported`, `generation_attempts`, `trace`), contains `None` for non-nullable fields, or passes invalid field types (e.g. string for `is_supported`), the route boundary treats this as an internal contract violation and returns **HTTP 500 Internal Server Error**.

> **Interview Takeaway:**
> "The HTTP transport layer translates valid application outcomes, but it must not manufacture fallback answers or coerce types to compensate for malformed runtime state. A valid safe refusal is an explicit application entity (`AnswerStatus.UNSUPPORTED`), whereas an incomplete terminal state is an operational failure."

---

## Future Evolution & Out of Scope (Design-Only)

The following enterprise capabilities are deliberately deferred to future passes:
* **Token & Event Streaming**: SSE / WebSockets for streaming tokens or node events (Generator currently returns complete `Answer`).
* **Authentication & Authorization**: API Key / OAuth2 / JWT bearer tokens.
* **Rate Limiting & Tenant Context**: Per-tenant rate limiting and context propagation.
* **Distributed Observability**: OpenTelemetry HTTP middleware and request correlation IDs.
* **Horizontal Scaling & Persistence**: Migrating single-file SQLite to PostgreSQL for multi-replica ASGI deployments.

---

## Technical Interview Questions & Answers

### Q1: Why shouldn't FastAPI route handlers call LLMs or vector stores directly?
**Answer:** Exposing LLMs or vector stores directly inside HTTP route handlers tightly couples transport concerns to AI orchestration logic. Keeping route handlers thin allows the exact same `CorrectiveRAGApplication` runtime to be driven by web APIs, CLI tools, unit tests, background queues, or scheduled jobs without duplicating orchestration or persistence rules.

### Q2: Why is safe refusal returned as HTTP 200 instead of HTTP 400/404?
**Answer:** Safe refusal occurs when evidence is insufficient or ungrounded. This is a successful application outcome representing an authoritative decision that the system cannot answer safely. HTTP status codes represent transport and protocol outcomes, not domain-level AI evidence grading results.

### Q3: Why return a custom response DTO instead of returning LangGraph `GraphState` directly?
**Answer:** `GraphState` is an internal application orchestration container that holds intermediate execution artifacts (candidate documents, intermediate search reformulations, internal graph flags). Exposing `GraphState` directly leaks application internals into the API contract, making future graph refactoring a breaking API change.

### Q4: How would you scale this API horizontally across multiple nodes?
**Answer:** To scale horizontally behind a load balancer:
1. Keep the FastAPI service stateless.
2. Replace single-file `SQLiteDecisionTraceRepository` with `PostgresDecisionTraceRepository` implementing the same `DecisionTraceRepository` Domain port.
3. Use a shared vector database cluster (e.g. Qdrant / Pgvector) and centralized provider client settings.
