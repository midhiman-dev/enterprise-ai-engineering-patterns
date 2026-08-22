# ADR-003: Groq as the Initial Hosted Generation Provider

## Status

Accepted

## Context

The Corrective RAG learning system requires a real hosted LLM provider to demonstrate candidate answer generation grounded in retrieved evidence documents.

To preserve Clean Architecture principles and learner diagnostic clarity:
* Provider coupling must remain isolated within the Infrastructure layer.
* Domain and Application layers must remain completely provider-neutral.
* Unit and graph orchestration tests must remain deterministic, fast, and 100% offline.
* Live cloud API smoke tests must be strictly opt-in to prevent CI breakage, rate-limiting failures, or mandatory API key setup for learners.

## Decision

We adopt **Groq** (via the official `groq` Python SDK) as the initial concrete hosted implementation for the Domain `Generator` port (`GroqGenerator`).

### Architectural Rules
1. **Capability Isolation**: `GroqGenerator` implements only the candidate generation capability (`Generator`). It does NOT act as a monolithic "GroqAIService" that absorbs relevance grading, query rewriting, or hallucination checking. Future capabilities will receive their own dedicated adapters.
2. **Structural Dependency Inversion**: `GroqGenerator` structurally satisfies the Domain `Generator` protocol without inheriting from it. Application orchestration depends solely on the `Generator` port interface.
3. **Internal Testing Boundary**: An internal Infrastructure-only client protocol (`GroqChatClient`) and wrapper (`GroqSdkChatClient`) are used to decouple `GroqGenerator` from raw SDK client instantiation, allowing fast offline unit testing via handwritten in-memory fake clients.
4. **Environment Configuration**: Secrets and model options are managed via `GroqConfig` loaded from environment variables (`GROQ_API_KEY`, `GROQ_MODEL`). Unset or blank keys fail immediately during configuration loading before any network call is attempted.

## Alternatives Considered

### 1. Groq (Selected)
* **Pros**: Generous free tier suitable for hands-on learning, extremely low latency (fast token generation), simple chat completions API, hosted LLM infrastructure requiring zero local GPU setup.
* **Trade-offs**: API rate limits on free tier, external network dependency for live tests, potential model catalog deprecations over time.

### 2. OpenAI API
* **Pros**: Industry-standard API ecosystem, highly mature tooling.
* **Trade-offs**: Requires active paid billing setup and API credentials for learners, creating friction for tutorial execution.

### 3. Ollama (Local LLMs)
* **Pros**: 100% private, offline execution, no API key required.
* **Trade-offs**: Requires substantial local hardware (RAM/GPU), multi-gigabyte model downloads, and additional background service setup for learners.

## Consequences

* **Positive**:
  * Learners can execute candidate answer generation using hosted models on a free tier.
  * Graph execution tests remain completely offline and deterministic using fake client injection.
  * Replacing Groq with another generator provider (e.g. OpenAI or Ollama) requires zero changes to Domain ports or Application graph nodes, provided the replacement provider preserves the semantics of the existing `Generator` port contract.
  * *Note on Contract Evolution*: Dependency inversion isolates vendor implementation details, but it does not mean all providers are behaviorally interchangeable without contract changes. Materially different capability requirements (such as token streaming, structured JSON output, multimodal inputs, native tool calling, or citation metadata) would legitimately require evolving the Domain port contract.

* **Negative / Risks**:
  * Live smoke tests depend on external Groq API availability and network connectivity.

## Senior Interview Takeaway

> "I isolate hosted model providers behind capability-specific ports. `Generator` is separate from grading, query rewriting, or hallucination checking because these capabilities often have vastly different latency requirements, cost profiles, prompt strategies, and model selection criteria. A monolithic AI service class tightly couples disparate business responsibilities to a single vendor."
