# ADR-007: Evidence Grounding Verification for Generated Answers

* **Status:** Accepted
* **Date:** 2026-08-22
* **Deciders:** AI Engineering Team

---

## Context & Problem Statement

In Retrieval-Augmented Generation (RAG) systems, retrieving relevant documents does not automatically guarantee that the generated candidate answer will be faithful to or grounded in those documents.

A candidate LLM generator can still:
* Fabricate plausible technical commands, flags, APIs, configuration settings, or remediation steps absent from the retrieved material (e.g., inventing `--enable-quantum-scheduler`).
* Contradict established facts inside the evidence documents.
* Rely on ungrounded model prior knowledge or hallucinated premises.
* Over-generalize or omit crucial caveats established in the evidence.

Before a generated answer is returned to the user or committed as an final workflow state, the system requires an explicit verification mechanism to assess whether the answer is supported by the retrieved evidence.

---

## Decision Driver & Learning Distinction

A critical AI-engineering distinction must be maintained:

> **Grounding / Support Verification $\neq$ Universal Real-World Fact Checking**

* **Grounding Checker Scope:** Answers *'Is this candidate answer supported by the supplied evidence documents?'*
* **Fact Checker Scope:** Answers *'Is this answer universally true in the real world?'*

If the supplied evidence documents themselves are stale, incomplete, or inaccurate, a grounding checker will still mark a faithful answer as `is_supported = True`. The grounding verifier operates strictly as an entailment evaluator against the workflow's evidence boundary.

---

## Proposed Architectural Solution

We implement a concrete infrastructure adapter, `GroqHallucinationChecker`, implementing the Domain `HallucinationChecker` port contract:

```python
class HallucinationChecker(Protocol):
    def is_supported(
        self,
        answer: Answer,
        documents: Sequence[Document],
    ) -> bool:
        ...
```

### Key Adapter Components
1. **Prompt-Constrained JSON Output**: The model is instructed to output ONLY a single JSON object with exact keys `{"is_supported": bool, "reason": str}`.
2. **Defensive Prompting (Evidence-as-Data Defense)**: The prompt explicitly instructs the model to treat retrieved documents as untrusted reference material. System instructions inside document text must never alter evaluation rules or format constraints.
3. **Strict Application-Side Validation**: The parser (`parse_grounding_result`) validates JSON structure, exact keys, and strict boolean types without coercion, throwing `RuntimeError` if model output deviates.
4. **Input Invariant Enforcement**: Calling `is_supported` with an empty document list (`documents=[]`) raises `ValueError` immediately, distinguishing an invalid adapter invocation from a legitimate unsupported candidate answer.

---

## Alternatives Considered

### 1. No Separate Checker (Trust Generator Output)
* **Pros:** Lowest latency, minimal token consumption.
* **Cons/Trade-offs:** High risk of serving ungrounded or fabricated technical claims to enterprise users.

### 2. Generator Self-Assessment in the Same Prompt
* **Pros:** Single LLM call, reduced latency compared to dual-call patterns.
* **Cons/Trade-offs:** Lacks independent evaluation context, obscures graph observability, degrades testability, and risks generator self-confirmation bias.

### 3. Separate LLM Grounding Verifier (Selected)
* **Pros:** Explicit graph stage, independent prompt responsibility, fully auditable routing decisions in LangGraph, testable with mock/fake clients, and allows decoupling the generator model from the verifier model.
* **Cons/Trade-offs:** Adds latency and additional provider token cost per generation attempt.

### 4. Deterministic NLI / Entailment Cross-Encoder Model
* **Pros:** Deterministic, low latency, lower operational cost, special-purpose training for natural language inference.
* **Cons/Trade-offs:** Requires hosting dedicated NLI models (e.g. DeBERTa), and may struggle with complex multi-document technical reasoning without extensive fine-tuning.

---

## Failure & Operational Semantics

| Condition | Result / Action | Operational Meaning |
| :--- | :--- | :--- |
| **Evidence supports answer** | `is_supported() -> True` | Workflow completes successfully (`END`). |
| **Evidence lacks support / contradicts** | `is_supported() -> False` | Workflow routes to query rewriting / fallback search or safe refusal. |
| **Empty document list (`[]`)** | `raise ValueError` | Invalid call parameters; caller passed no evidence to verify against. |
| **API network / auth error** | `raise RuntimeError` | Provider infrastructure failure; propagated without collapsing to `False`. |
| **Malformed JSON output** | `raise RuntimeError` | Verification pipeline failure; output contract violated. |

---

## Production Evolution (Design Only)

In production enterprise deployments, grounding verification can evolve beyond single-pass LLM prompts:
1. **Claim Decomposition**: Break candidate answers into atomic propositions and evaluate grounding per proposition.
2. **Per-Claim Citation Binding**: Require inline citations linking every technical assertion directly to specific document chunks.
3. **Hybrid Verification**: Combine fast local NLI cross-encoders for simple claims with LLM verifiers for complex multi-document synthesis.
4. **Calibrated Evaluation Suites**: Benchmark verifier precision/recall using curated golden datasets containing subtle numerical mismatches, missing prerequisites, and fabricated flags.

---

## Technical Interview Questions & Answers

### Q1: Is a hallucination checker a fact checker?
**Answer:** No. A hallucination / grounding checker evaluates whether a candidate answer is supported by the specific evidence documents supplied to it. It does not verify universal real-world truth. If the evidence itself contains an error or stale documentation, a correctly functioning grounding checker will still mark the faithful answer as supported.

### Q2: Why not ask the Generator to self-check in the same prompt?
**Answer:** Decoupling generation and verification provides independent prompt context, explicit graph state transitions in LangGraph, isolated unit testability, clear observability in decision traces, and the flexibility to use different models or specialized NLI verifiers.

### Q3: Can the same model generate and verify?
**Answer:** Yes. In Pass-11, the same Groq model configuration (`llama-3.3-70b-versatile`) is used for both generation and grounding verification. However, Clean Architecture keeps the *capability port* (`HallucinationChecker`) decoupled from the *provider deployment choice*, allowing team optimization later.
