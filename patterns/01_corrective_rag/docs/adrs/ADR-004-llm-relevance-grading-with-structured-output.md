# ADR-004: LLM Relevance Grading with Validated JSON Output

## Status

Accepted

## Context

The Corrective RAG (CRAG) workflow requires an explicit relevance evaluation step following candidate retrieval.

Vector similarity search (e.g. via Chroma) returns nearest-neighbor candidate chunks based on embedding proximity. However:
* **Vector similarity distance does NOT equal answer relevance.** A retrieved document may be vector-near due to domain keyword density (e.g., broad Kubernetes terminology) yet fail to contain the specific diagnostic evidence needed to answer the user's question.
* Downstream orchestration must decide whether to proceed with retrieved evidence or trigger corrective action (such as web search).

To keep the system robust, readable, and auditable:
* Document grading must happen after retrieval on a single document at a time.
* The model is instructed through the prompt to return JSON-formatted text:
  ```json
  {
    "is_relevant": true,
    "reason": "..."
  }
  ```
* The response is parsed with Python's standard `json.loads()` and strictly validated by application code for exact expected keys (`{"is_relevant", "reason"}`), strict boolean type checking, non-blank string rationale, malformed JSON, and unexpected fields.
* **The provider itself is not enforcing a JSON Schema in Pass-8.** We intentionally use prompt-constrained JSON with application-side response validation rather than provider-native schema enforcement to keep the provider client boundary (`GroqChatClient`) simple and visible.
* Provider errors or malformed model responses raise operational infrastructure errors (`RuntimeError`) rather than silently coercing provider failures into `is_relevant=False` business decisions.

## Decision

We implement **`GroqRelevanceGrader`** as a concrete Infrastructure adapter for the Domain `RelevanceGrader` port using prompt-constrained JSON and strict application-side validation via Groq.

### Key Architectural & Contract Rules

1. **Validated JSON Contract**: The model is prompted to emit a JSON object (`{"is_relevant": true|false, "reason": "..."}`), but correctness is enforced after generation by our parser and validation logic (`parse_relevance_result`).
   - `is_relevant`: `bool` (strictly `type(val) is bool`).
   - `reason`: `str` (non-empty string rationale explaining the decision).
   Unexpected keys, missing fields, or incorrect data types (e.g. `"is_relevant": "yes"`) trigger validation failures.

2. **Probabilistic Generation vs. Deterministic Validation**:
   ```text
   probabilistic LLM generation
              ↓
   deterministic parser / validator
              ↓
   validated machine-readable boolean decision
   ```
   The LLM relevance judgment itself remains probabilistic. What becomes deterministic is JSON parsing, type validation, and downstream graph branching once a valid result exists.

3. **No Undefined Numeric Confidence Score**: The internal grading result maps to `GradedDocument` with `score=None`. We do not invent an arbitrary 0.0–1.0 numeric score because numeric confidence metrics require calibrated domain semantics before they can be interpreted meaningfully.

4. **Standard Library Parsing & Client Boundary Discipline**: Validation uses Python's standard `json` module without introducing heavy external runtime validation libraries (such as Pydantic or Instructor). We intentionally reuse the existing minimal `GroqChatClient.complete(model, messages, temperature)` abstraction to prioritize visible learning mechanics without prematurely expanding vendor-specific client capabilities.

5. **Strict Operational Error Handling**: Provider API failures or invalid model outputs raise `RuntimeError` operational exceptions. Infrastructure errors are never silently swallowed or converted into `is_relevant=False`.

## Alternatives Considered

### 1. Prompt-Constrained JSON + Strict Validation (Selected)
* **Pros**: Explicit machine-readable contract, high semantic understanding of question-document evidence relationships, clear audit rationale (`reason`), complete isolation from provider specifics behind Domain port, no vendor SDK lock-in for schema enforcement.
* **Trade-offs**: Requires LLM invocation latency and API cost per candidate document; response format compliance relies on prompt following and application-side validation.

### 2. Vector Distance Threshold Only
* **Pros**: Zero additional LLM API call cost or latency.
* **Trade-offs**: Flawed assumption. Embedding distance measures global vector proximity, not task-specific evidence utility. Thresholds vary unpredictably across indices, embedding models, and chunking strategies.

### 3. Rule-Based / Keyword Overlap Grader
* **Pros**: Fast, deterministic, zero cost.
* **Trade-offs**: High false positives/negatives in complex technical domains (e.g. Kubernetes), as lexical overlap does not capture semantic intent.

### 4. LLM Free-Form Text Response Parsing (Substring Matching)
* **Pros**: Simple prompt instruction.
* **Trade-offs**: Fragile and error-prone. LLMs frequently format output unpredictably (e.g., "Yes, however...", "True, but..."), leading to parsing ambiguities.

## Important Conceptual Distinction: Retrieval Distance vs. Relevance Grade

```
Chroma Vector Retrieval           LLM Relevance Grader
------------------------           --------------------
Candidate Recall Optimization     Semantic Evidence Validation
"Nearest in embedding space"  !=  "Contains evidence needed to answer question"
```

Vector retrieval optimizes candidate recall across large document corpora. Relevance grading evaluates whether a specific candidate actually contains the evidence required to answer the prompt.

## Consequences

* **Positive**:
  * Orchestration operates on a validated, machine-readable boolean decision rather than guessing intent from LLM prose.
  * Graph tests remain 100% offline and deterministic using fake client injection.
  * Provider API failures are explicitly distinguishable from negative grading outcomes.

* **Negative / Risks**:
  * Grading each document sequentially adds LLM latency during the evaluation phase.

## Production Evolution (Design-Only — Not Implemented in Pass-8)

### Provider-Native Structured Output

In a production enterprise deployment, relevance grading can evolve to leverage provider-native structured output features where supported:

```text
Current Pass-8 (Prompt-Constrained JSON):
  prompt requests JSON → text response → json.loads() → application validation → domain result

Possible Production Evolution (Provider-Native Structured Output):
  prompt + provider schema/response_format → provider-constrained response → application validation → domain result
```

Key considerations for production evolution:
* **Provider-Native Schema Enforcement**: Where supported by the model provider (e.g. JSON response mode, `response_format` with JSON Schema), schema constraints are enforced during token sampling.
* **Continued Boundary Validation**: Even if a provider guarantees structured output, application-side boundary validation remains mandatory to protect domain entities from upstream schema drift or API contract changes.
* **Client Abstraction Evolution**: If future capabilities genuinely require provider-native schema enforcement, the `GroqChatClient` infrastructure interface can be deliberately extended without impacting Domain or Application layers.
* **Model Selection & Batching**: Using a smaller, cheaper model for grading (e.g., Llama-3-8B) and grading multiple retrieved candidates concurrently to minimize latency.

## Senior Interview Takeaway

> "I distinguish between asking an LLM to return JSON and using provider-enforced structured output. In this implementation the prompt requests JSON, then I parse and strictly validate the response before orchestration consumes it. In production I would evaluate provider-native JSON Schema or response-format enforcement where supported, but I would still validate the result at my application boundary."
