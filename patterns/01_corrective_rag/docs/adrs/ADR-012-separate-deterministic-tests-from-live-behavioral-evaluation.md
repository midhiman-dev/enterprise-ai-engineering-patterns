# ADR-012: Separate Deterministic Tests from Live Behavioral Evaluation

* **Status:** Accepted
* **Date:** 2026-08-31
* **Layer:** Testing / Evaluation / System Boundary

---

## Context

Testing enterprise RAG and Corrective RAG (CRAG) systems presents a fundamental tension:
- **Unit and Integration Tests** must be fast, deterministic, reproducible, and run offline in CI/CD without requiring external network connectivity or paid API credentials.
- **Provider Smoke Tests** must verify real external API connectivity, authentication, and SDK response parsing against actual third-party infrastructure (e.g. Groq, Tavily).
- **Assembled-System Behavioral Evaluation** must evaluate how the full system behaves when given end-to-end user queries against real vector stores and probabilistic LLM providers.

If an architecture relies solely on unit tests with handwritten fakes, it cannot detect when hosted LLM providers retire models (as observed in Pass-15B) or when retrieval grading fails on ambiguous text. Conversely, if live external API calls are forced into default CI test suites, builds become flaky, slow, expensive, and fragile.

---

## Decision

We establish three distinct, complementary validation layers for the Corrective RAG architecture:

1. **Layer 1: Deterministic Offline Tests (`python -m pytest`)**
   - **Scope**: Unit tests for Domain entities, Application state transitions, LangGraph node handlers, and Infrastructure adapters using handwritten fakes/stubs.
   - **Properties**: 100% offline, zero network access, fast (< 5s), zero API cost, deterministic outcome.
   - **Execution**: Run automatically on every build and CI invocation.

2. **Layer 2: Opt-in Live Adapter Smoke Tests (`python -m pytest tests/live -m live`)**
   - **Scope**: Single-component live connectivity and protocol contract tests against real Groq and Tavily endpoints.
   - **Properties**: Opt-in via pytest `-m live` marker, requires valid `GROQ_API_KEY` and `TAVILY_API_KEY`.
   - **Execution**: Run manually or in scheduled integration pipelines to detect provider API breaks or model deprecations.

3. **Layer 3: Opt-in Live Assembled-System Golden Evaluation (`python scripts/evaluate_golden_scenarios.py --live`)**
   - **Scope**: Observational, non-invasive behavioral evaluation of the full assembled application (`build_application() -> CorrectiveRAGApplication.run(...)`) against defined golden query scenarios (Q1, Q2, Q3).
   - **Properties**: Requires explicit `--live` CLI flag, validates runtime prerequisites (Chroma collection existence and non-emptiness), records observable DecisionTrace steps and evidence without forcing graph routing, and persists timestamped evaluation JSON artifacts under `artifacts/evaluations/`.
   - **Execution**: Run on-demand to capture baseline behavioral evidence and trace system evolution over time.

---

## Alternatives Considered

### 1. Unified Test Suite Calling Live External APIs in Default `pytest`
- **Rejected**.
- **Reason**: Causes CI builds to fail whenever external APIs experience transient network issues, rate limits, or latency spikes. Exposes paid API keys in unauthenticated test environments.

### 2. Pure Mock-Only Testing (No Live System Evaluation)
- **Rejected**.
- **Reason**: Fails to prove that the assembled system works with real embedding models, real vector retrieval, real search search, and real LLM reasoning. Missed model deprecations (such as Groq model availability changes).

### 3. Route-Forcing Evaluation (Hardcoding Expected Paths into System Logic)
- **Rejected**.
- **Reason**: Violates Clean Architecture and learner-first principles by disguising synthetic test logic as genuine production routing. Evaluation must observe system behavior, not dictate it.

---

## Rationale & Key Architectural Insights

### Observational Evaluation vs. Route Forcing
The evaluation harness acts strictly as an external consumer of the `CorrectiveRAGApplication` public boundary. It inspects the returned `GraphState` and `DecisionTrace` to record observed node progression, document relevance decisions, rewritten queries, and final answer status. It never special-cases query strings inside graph routing nodes or alters prompts to force a preferred outcome.

### Failure Classification vs. System Divergence
Evaluation outcomes distinguish between:
- **PASS**: The observed system behavior aligns with scenario hypothesis properties.
- **DIVERGENCE**: The system produced a valid result, but routed differently than hypothesized (e.g. Q2 local docs evaluated relevant by LLM grader). This represents valuable behavioral evidence for future tuning rather than a code defect.
- **ERROR**: An unhandled runtime exception or provider failure occurred.

---

## Consequences

### Positive
- Ordinary CI test execution remains blazingly fast and deterministic.
- Production code remains completely decoupled from evaluation logic.
- Real system baseline performance and divergences are recorded truthfully in structured artifacts.

### Negative / Trade-offs
- Live evaluations are subject to external API availability, cost, and LLM non-determinism.
- Three golden queries provide qualitative qualitative behavioral evidence but do not constitute a statistically comprehensive retrieval benchmark.
