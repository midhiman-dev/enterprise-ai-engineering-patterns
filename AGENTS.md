# AGENTS.md — AI Coding Assistant Guardrails & Conventions

This repository, `enterprise-ai-engineering-patterns`, is a **hands-on Python AI engineering learning repository**.

Its goal is to teach how realistic enterprise AI systems are engineered using readable Python, Clean Architecture (Ports & Adapters), explicit orchestration, comprehensive testing, observability, and production-oriented design.

All AI coding assistants generating or modifying code in this repository MUST strictly follow these rules.

---

## 1. Learner-First Code Style

Code is written primarily to be read, understood, and audited by learners.

### Prefer
* **Straightforward Python**: Write idiomatic, readable code over clever solutions.
* **Descriptive Names**: Name variables, functions, classes, and modules explicitly to reflect business domain concepts.
* **Explicit Types**: Use Python type hints (`typing`) for function parameters, return values, and data structures.
* **Small Cohesive Functions**: Keep functions focused on a single responsibility.
* **Understandable Control Flow**: Prefer explicit `if/else` and match blocks over complex abstractions or implicit dispatch.
* **Conventional Python Constructs**: Use standard standard-library capabilities (`dataclasses`, `enum`, `abc`, `typing`).
* **Simple Dependency Injection**: Pass dependencies explicitly via class `__init__` or function arguments.
* **Comments Explaining "Why"**: Comment on intent, architectural rationale, or domain constraints—not self-evident code mechanics.
* **Docstrings**: Provide docstrings on public modules, interfaces (ports), and complex functions where intent or contract is non-obvious.

### Avoid
* Clever one-liners or cryptic list comprehensions
* Excessive custom decorators or magic
* Metaprogramming, standard-library hacks, or `__getattr__` dynamic dispatch
* Unnecessary generic typing complexity
* Unnecessary class inheritance or deep class hierarchies
* Speculative extension frameworks or plugin systems
* Custom mini-frameworks built on top of standard libraries
* Premature optimization
* Unnecessary design patterns (e.g., complex abstract factories where simple constructors suffice)

### The 4 Learner Diagnostic Questions
A learner reading any source file in this repository should be able to quickly answer:
1. **What does this file do?**
2. **Why does it belong in this architectural layer?**
3. **What dependency does it need?**
4. **What would change if that dependency were replaced?**

---

## 2. Framework Visibility

Do **not** hide core framework concepts behind unnecessary generic wrappers or custom mini-frameworks.

When demonstrating an orchestration framework like **LangGraph**:
* Learners must directly see and understand:
  * Graph state schemas
  * Node handler signatures and logic
  * Graph edge definitions
  * Conditional routing logic
  * Retry and fallback policies
  * Termination conditions
  * Graph compilation
* Clean Architecture isolates external data/AI providers (e.g., Chroma, Tavily, OpenAI, Ollama), **not** the AI orchestration framework being taught.
* Orchestration lives in the **Application layer** and directly uses framework abstractions while invoking Domain ports for external capabilities.

---

## 3. Small Architectural Slices

* Execute work strictly in small, well-bounded passes/slices.
* **Never** implement multiple architectural slices or future features merely because they are easy to generate.
* Stick strictly to the active pass scope.
* **Do not** begin subsequent passes automatically. Stop and report completion after each pass.

---

## 4. Dependency Discipline

* Do **not** introduce third-party dependencies unless the active pass explicitly requires them.
* Do **not** add libraries "for future use" or "just in case".
* Keep the Domain layer **100% pure Python** with zero third-party dependencies.

---

## 5. Testing Discipline

* Every behavior introduced in future passes must include appropriately scoped tests:
  * `unit/domain` for pure domain logic and entities
  * `unit/application` for orchestration, state transitions, and routing (using port mocks)
  * `integration/infrastructure` for external adapter implementations
  * `acceptance` for end-to-end golden scenarios
* Tests must communicate system behavior and contracts, not merely exist for test coverage metrics.
* Never create dummy test assertions (e.g., `assert True`).

---

## 6. Documentation Truthfulness

* **Never** document something as implemented, production-ready, benchmarked, or verified unless the repository code actually proves it.
* Keep status badges, README files, and tutorials synchronized with verified repository code.
* Do not invent hypothetical benchmark figures or claim test coverage that does not exist.

---

## 7. No Silent Architecture Changes

* Architectural layer boundaries and ADRs are binding contracts.
* If an implementation appears to require altering an established boundary or ADR, **stop immediately** and report the conflict to the user instead of silently redesigning the architecture.
