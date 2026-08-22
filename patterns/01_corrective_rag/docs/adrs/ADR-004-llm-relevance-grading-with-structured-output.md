# ADR-004: LLM-Based Relevance Grading with Structured Output

## Status

Accepted

## Context

The Corrective RAG (CRAG) workflow requires an explicit relevance evaluation step following candidate retrieval.

Vector similarity search (e.g. via Chroma) returns nearest-neighbor candidate chunks based on embedding proximity. However:
* **Vector similarity distance does NOT equal answer relevance.** A retrieved document may be vector-near due to domain keyword density (e.g., broad Kubernetes terminology) yet fail to contain the specific diagnostic evidence needed to answer the user's question.
* Downstream orchestration must decide whether to proceed with retrieved evidence or trigger corrective action (such as web search).

To keep the system robust, readable, and auditable:
* Document grading must happen after retrieval on a single document at a time.
* The model output must follow a strict, machine-readable JSON structure rather than fragile free-form text parsing (e.g. matching substrings like "yes" or "true").
* Provider errors or malformed model responses must raise operational infrastructure errors rather than silently coercing provider failures into `is_relevant=False` business decisions.

## Decision

We implement **`GroqRelevanceGrader`** as a concrete Infrastructure adapter for the Domain `RelevanceGrader` port using structured JSON evaluation via Groq.

### Key Architectural & Contract Rules

1. **Structured Output Contract**: The model is instructed to return strictly a JSON object with:
   - `is_relevant`: `bool` (required boolean value).
   - `reason`: `str` (non-empty string rationale explaining the decision).
   Unexpected keys, missing fields, or incorrect data types (e.g. `"is_relevant": "yes"`) trigger validation failures.

2. **No Undefined Numeric Confidence Score**: The internal grading result maps to `GradedDocument` with `score=None`. We do not invent an arbitrary 0.0–1.0 numeric score because numeric confidence metrics require calibrated domain semantics before they can be interpreted meaningfully.

3. **Standard Library Parsing**: Validation uses Python's standard `json` module without introducing heavy external runtime validation libraries (such as Pydantic or Instructor).

4. **Strict Operational Error Handling**: Provider API failures or invalid model outputs raise `RuntimeError` operational exceptions. Infrastructure errors are never silently swallowed or converted into `is_relevant=False`.

## Alternatives Considered

### 1. Structured LLM Grading (Selected)
* **Pros**: Explicit machine-readable contract, high semantic understanding of question-document evidence relationships, clear audit rationale (`reason`), complete isolation from provider specifics behind Domain port.
* **Trade-offs**: Requires LLM invocation latency and API cost per candidate document.

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
  * Orchestration operates on a validated, deterministic boolean decision rather than guessing intent from LLM prose.
  * Graph tests remain 100% offline and deterministic using fake client injection.
  * Provider API failures are explicitly distinguishable from negative grading outcomes.

* **Negative / Risks**:
  * Grading each document sequentially adds LLM latency during the evaluation phase.

## Production Evolution (Design-Only — Not Implemented in Pass-8)

In a production enterprise deployment, relevance grading can evolve through:
* **Model Selection**: Using a smaller, cheaper, faster model for grading (e.g., Llama-3-8B) while using a larger model for candidate generation.
* **Batched / Parallel Grading**: Grading multiple retrieved candidates concurrently to reduce latency.
* **Reranking Models**: Inserting a cross-encoder reranker before LLM grading to filter candidate count.
* **Dataset Evaluation**: Calibrating grading prompt performance against labeled golden relevance datasets.

## Senior Interview Takeaway

> "I separate retrieval candidate selection from semantic relevance validation. Vector search optimizes recall using embedding proximity, but vector distance does not guarantee answer relevance. The relevance grader evaluates whether each candidate actually contains evidence needed for the user's question. I use structured output parsing so downstream orchestration consumes a validated boolean decision rather than parsing free-form LLM prose."
