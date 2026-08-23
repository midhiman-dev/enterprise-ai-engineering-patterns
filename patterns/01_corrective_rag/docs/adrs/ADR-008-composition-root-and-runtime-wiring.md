# ADR-008: Composition Root and Real Adapter Runtime Wiring

* **Status:** Accepted
* **Date:** 2026-08-23
* **Deciders:** AI Engineering Team

---

## Context & Problem Statement

Through Pass-11, all essential components of the Corrective RAG system have been implemented:
* **Domain Layer:** Defines pure entities (`Question`, `Document`, `Answer`) and core capability contracts / ports (`Retriever`, `RelevanceGrader`, `QueryRewriter`, `Generator`, `WebSearchProvider`, `HallucinationChecker`).
* **Application Layer:** Orchestrates graph execution flow (`GraphState`, node handlers, routing logic) via `WorkflowDependencies` container and `build_graph()`.
* **Infrastructure Layer:** Implements concrete provider adapters (`ChromaRetriever`, `GroqRelevanceGrader`, `GroqQueryRewriter`, `GroqGenerator`, `TavilyWebSearchProvider`, `GroqHallucinationChecker`).

However, until Pass-12, no single module existed to choose and assemble these concrete implementations together into an executable application graph. 

Clean Architecture requires that:
1. Domain abstractions remain independent of concrete infrastructure details.
2. Application orchestration logic depends only on Domain capability ports.
3. Infrastructure adapters implement Domain ports without introducing cross-layer dependencies.

Eventually, something in the system MUST know about concrete classes and choose which implementations run together. That responsibility belongs strictly to the **Composition Root**.

---

## Decision

We establish an explicit Python Composition Root in `src/corrective_rag/composition/` consisting of:
1. `ApplicationSettings` & `load_application_settings_from_env()`: Parsed, validated application composition configuration (`chroma_path`, `chroma_collection`, `retriever_top_k`).
2. `build_dependencies(...)`: Constructs real concrete Infrastructure adapters (`ChromaRetriever`, `GroqRelevanceGrader`, `GroqQueryRewriter`, `GroqGenerator`, `TavilyWebSearchProvider`, `GroqHallucinationChecker`) and packages them into `WorkflowDependencies`.
3. `build_application(...)`: Calls `build_dependencies(...)` and compiles the application graph using `build_graph(...)`.

```
ApplicationSettings + Provider Configs (GroqConfig, TavilyConfig)
                    ↓
        Infrastructure Adapters
                    ↓
          WorkflowDependencies
                    ↓
         build_graph(dependencies)
                    ↓
         Compiled LangGraph App
```

---

## Shared Provider Resources vs. Capability Separation

The application uses four distinct Groq-backed capability adapters:
* `GroqGenerator` (satisfies `Generator`)
* `GroqRelevanceGrader` (satisfies `RelevanceGrader`)
* `GroqQueryRewriter` (satisfies `QueryRewriter`)
* `GroqHallucinationChecker` (satisfies `HallucinationChecker`)

While each adapter maintains a distinct semantic responsibility and satisfies a separate Domain interface, the Composition Root instantiates a **single shared `GroqSdkChatClient`** and `GroqConfig` instance, injecting them into all four adapters.

> **Key Takeaway:** Capability interface separation does NOT require network client or transport connection duplication. The Domain enforces Interface Segregation, while the Composition Root manages resource lifecycles efficiently.

---

## Configuration Boundary and Fail-Fast Semantics

Environment variable resolution occurs strictly during startup inside configuration loader functions (`load_application_settings_from_env()`, `load_groq_config_from_env()`, `load_tavily_config_from_env()`).

* Business and application logic never invoke `os.getenv()` during execution.
* Defaults apply when an optional environment variable is absent (`os.getenv(...) is None`). An explicitly configured blank or whitespace-only value (`""`, `" "`) is treated as invalid configuration and causes startup to fail fast with `ValueError`.
* If required API keys (`GROQ_API_KEY`, `TAVILY_API_KEY`) or invalid composition settings (`retriever_top_k <= 0`) are encountered, composition **fails fast** with an explicit exception during startup.
* Production composition never falls back to test doubles or placeholder keys.


---

## Alternatives Considered

### Alternative 1: Explicit Composition Root (Selected)
* **Pros:** Transparent, learner-friendly, zero magical framework overhead, easy to trace execution and wire dependency seams for testing.
* **Cons:** Manual parameter passing when instantiating adapters.

### Alternative 2: Third-Party Dependency Injection (DI) Framework (e.g. `dependency-injector`, `Injector`)
* **Pros:** Automatic lifecycle management, decorated injection bindings.
* **Cons:** Hides wiring mechanics behind framework annotations/magic, adds external runtime dependencies, creates unnecessary complexity for a focused tutorial codebase.

### Alternative 3: Construct Adapters Inside Web Framework Routes (e.g., FastAPI handlers)
* **Pros:** Simple initial setup for web developers.
* **Cons/Trade-offs:** Severely couples HTTP route handlers to concrete infrastructure providers, creates per-request construction overhead, duplicates wiring logic across endpoints, and makes testing state graphs difficult.

### Alternative 4: Construct Providers Inside LangGraph Nodes
* **Pros:** No external container passed into node factories.
* **Cons/Trade-offs:** Highly anti-pattern. Forces Application layer node handlers to import concrete provider SDKs (Groq, Tavily, Chroma), destroying Clean Architecture boundaries and preventing offline testing with fake adapters.

---

## Technical Interview Questions & Answers

### Q1: Why have a composition root if Clean Architecture promotes decoupling?
**Answer:** Clean Architecture does not eliminate coupling; it concentrates concrete coupling at the outermost application boundary. Dependency inversion means Domain and Application depend on capability contracts, while the Composition Root is deliberately the single place that knows concrete implementations and wires them together at application startup.

### Q2: Why not use a Dependency Injection framework?
**Answer:** An explicit Python composition root is easy to read, audit, and debug without framework magic. DI frameworks become beneficial when object graphs and lifetimes grow excessively complex, but architecture itself should never depend on a DI framework framework.

### Q3: Should I create a separate LLM client for each capability adapter?
**Answer:** No. Keeping capability interfaces separate (Interface Segregation) does not require duplicating low-level network clients or HTTP connection pools. Separate adapters can share a single underlying SDK client instance.
