# Contributing Guidelines

Thank you for contributing to `enterprise-ai-engineering-patterns`.

This repository exists to teach realistic, production-minded AI engineering through clear Python, explicit Clean Architecture boundaries, traceable orchestration, and testable design.

---

## Core Contribution Principles

### 1. Learner-First Code Quality
* Code must be readable, self-explanatory, and typed.
* Prefer explicit logic over clever, implicit, or magical abstractions.
* Include comments explaining **why** a non-obvious design decision was made.
* Ensure every source file clearly answers its purpose, layer boundary, and dependencies.

### 2. Strict Clean Architecture Dependency Flow
* The architectural dependency rule is strictly inward:
  ```text
  UI / API -> Application -> Domain <- Infrastructure
  ```
* **Domain is pure Python**: Absolutely NO imports of third-party SDKs or frameworks (e.g., LangChain, LangGraph, Chroma, OpenAI, Tavily, FastAPI, Pydantic, SQLAlchemy) in the Domain layer.
* Domain contains only pure entities, value objects, domain logic, and abstract port interfaces.
* Infrastructure implements Domain ports using external libraries and vendor SDKs.

### 3. Small, Bounded Slices
* Submit changes as focused, single-purpose passes or commits.
* Avoid massive pull requests that implement multiple unrelated features simultaneously.
* Do not introduce speculative code, unused helpers, or libraries "for future use."

### 4. Tests Accompany Behavior
* New behavior must be accompanied by appropriate automated tests:
  * Unit tests for pure domain logic and application orchestration (using mocks for ports).
  * Integration tests for infrastructure adapters.
  * Acceptance tests for end-to-end golden workflows.
* Do not add placeholder tests (`assert True`).

### 5. Architectural Decision Records (ADRs)
* Any meaningful architectural decision, boundary choice, or trade-off MUST be documented with an ADR in `docs/adrs/` using `docs/templates/ADR_TEMPLATE.md`.
* Never make silent architecture changes without updating or creating an ADR.

### 6. Truthful Documentation
* Documentation and tutorials must strictly reflect verified code in the repository.
* Do not invent fictional benchmarks, unverified setup instructions, or pseudo-code that differs from actual source implementations.
