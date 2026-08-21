# ADR-001: Clean Architecture and LangGraph Boundary

## Status

Accepted

## Context

When engineering AI systems with workflow orchestration frameworks like LangGraph, team architectures often drift into one of two extremes:

1. **Monolithic Framework Coupling**: LangGraph state, nodes, conditional edges, Chroma vector retrieval, Tavily search, and OpenAI SDK calls are all mixed directly into a single script or module. Direct vendor coupling makes application tests dependent on vendor SDK contracts or vendor-specific mocks and mixes orchestration concerns with integration concerns.
2. **Over-Abstraction**: Hiding LangGraph entirely behind custom, nested wrapper interfaces (e.g., an `IOrchestrator` abstraction hiding state, nodes, and edges). This obscures how LangGraph works, creating cognitive friction for learners wanting to learn LangGraph idioms.

We need an architectural decision that preserves **Clean Architecture provider isolation** while keeping **LangGraph orchestration visible and explicit** for learners.

## Decision

We will place **LangGraph workflow orchestration inside the Application layer**, allowing LangGraph graph state, nodes, edges, conditional routing, retries, and compilation to be directly visible in `corrective_rag.application`.

Crucially, LangGraph node functions will **not** import or invoke concrete SDKs (OpenAI, Chroma, Tavily, SQLite) directly. Instead, nodes will call abstract **Domain Ports** (e.g., `Retriever`, `RelevanceGrader`, `QueryRewriter`, `Generator`, `WebSearchProvider`, `HallucinationChecker`, `DecisionTraceRepository`). Concrete implementations of these ports will reside in `corrective_rag.infrastructure`.

## Alternatives Considered

### Alternative 1: Put LangGraph and all vendor SDK calls into a single application module
* *Pros*: Simple to write initially; minimal files.
* *Cons*: Violates Clean Architecture. Unit tests require network/vendor mocks or real API keys. Swapping Chroma or OpenAI requires rewriting graph node logic.

### Alternative 2: Hide LangGraph completely behind a generic orchestration abstraction
* *Pros*: Maximum theoretical decoupling from LangGraph itself.
* *Cons*: High abstraction penalty. Conceals core framework concepts (state, edges, retries, compilation) from learners, defeating the primary educational purpose of the repository.

### Alternative 3 (Selected): Keep orchestration visible in Application while isolating external capabilities behind Domain ports
* *Pros*: Achieves clean separation of concerns. The Application layer clearly teaches LangGraph mechanics; the Infrastructure layer isolates vendor SDKs; the Domain layer remains pure Python. Unit testing graph routing using mock ports requires no network calls.
* *Cons*: Requires introducing Domain port abstractions and explicit dependency injection at the Composition Root.

## Rationale

Selected Option 3 balances enterprise maintainability with the repository's educational objectives:
* Learners can open `corrective_rag.application` and directly study how LangGraph state transitions and conditional edges function.
* Enterprise maintainers can replace underlying vector stores (Chroma -> Qdrant), LLMs (OpenAI -> Ollama), or search providers (Tavily -> alternative) in `corrective_rag.infrastructure` without altering Domain or Application logic, provided the replacement preserves the semantics of the existing port contract. (If a replacement introduces materially different capabilities or contract semantics, the port/application design may legitimately need targeted evolution.)

## Trade-offs

* **Gained**: Testability (unit testing graph execution via port stubs), provider portability, clear architectural boundaries, explicit framework visibility.
* **Given up**: Extremely minimalistic single-file code structures (requires strict adherence to Clean Architecture folder layers).

## Consequences

* The `domain` package MUST remain 100% pure Python with zero third-party SDK imports.
* The `application` package MAY import LangGraph/LangChain core orchestration types, but MUST NOT import `chromadb`, `openai`, `tavily`, or concrete database drivers.
* The `infrastructure` package implements all Domain ports using vendor SDKs.
* Graph composition and dependency wiring are assembled strictly in `corrective_rag.composition`.

## Interview Takeaway

"When using workflow orchestration frameworks like LangGraph in enterprise applications, we don't hide the graph behind generic wrappers—doing so masks state transitions and graph routing logic. Instead, we place graph orchestration in the Application layer, while strictly isolating external AI and data providers (LLMs, vector databases, search APIs) behind Domain ports implemented in Infrastructure. Provided the replacement preserves port semantics, infrastructure providers can be swapped without rewriting application workflow logic."
