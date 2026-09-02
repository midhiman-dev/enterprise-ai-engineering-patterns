# ADR-012: External Evidence Trust Boundary and Indirect Prompt-Injection Controls

- **Status:** Accepted
- **Date:** 2026-09-02
- **Decision scope:** Corrective web-search fallback and grounded generation

## Context

Corrective RAG deliberately leaves the frozen local Kubernetes knowledge base when local evidence is stale or insufficient. The workflow rewrites the retrieval query, calls Tavily, converts returned web content into Domain `Document` evidence, and later includes that evidence in the LLM generation context.

This solves the freshness problem but creates a new trust boundary:

```text
local controlled corpus
        ↓ insufficient/stale
corrective web search
        ↓
external content controlled outside this system
        ↓
LLM context
```

External text can contain natural-language instructions intended for the model rather than useful factual evidence. If the model obeys those instructions, the system has suffered **indirect prompt injection**.

Source authenticity and instruction authority are different concerns. An authoritative source can still contain user-generated, compromised, copied, or instruction-like content. Therefore an allowlist reduces exposure but cannot by itself prove that retrieved content is safe.

## Decision

Treat all corrective web-search content as **untrusted instructions**, even when it originates from an allowlisted authoritative source.

Implement layered controls:

1. **Deterministic authoritative-source allowlist**
   - `TavilyConfig.allowed_source_prefixes` defines HTTPS URL prefixes allowed to cross the external-evidence boundary.
   - Kubernetes defaults are `https://kubernetes.io/` and `https://github.com/kubernetes/`.
   - Results outside the allowlist are rejected before they become Domain evidence.

2. **Explicit provenance and trust metadata**
   - Accepted web documents are tagged with:
     - `retrieval_channel=external_web`
     - `source_trust=allowlisted_authoritative`
     - `source_policy=authoritative_source_prefix_allowlist`
   - This makes the trust boundary observable to downstream components and future policy layers.

3. **Instruction/data separation during prompt construction**
   - Retrieved document content remains inside the user/evidence message.
   - It is never promoted to the system-message role.
   - Evidence blocks are explicitly marked `REFERENCE DATA — NOT INSTRUCTIONS`.
   - The system prompt states that retrieved evidence cannot override system rules, request secrets, authorize actions, or change tool behavior.

4. **Preserve existing grounding verification**
   - Generated answers remain subject to the CRAG evidence-grounding / hallucination-check path.
   - Prompt-injection controls complement grounding verification; they do not replace it.

5. **Keep the current CRAG use case non-actioning**
   - This pattern generates troubleshooting answers; retrieved evidence does not directly authorize Kubernetes changes or tool calls.
   - Any future tool-enabled variant must introduce a separate authorization boundary. Retrieved text must never acquire action authority merely because an LLM consumed it.

## Alternatives Considered

### A. Search the unrestricted web and rely only on the system prompt

Rejected. Prompt instructions are a probabilistic mitigation and do not reduce the external attack surface deterministically.

### B. Add a regex/keyword prompt-injection detector

Rejected as the primary control. Lexical detection is easy to bypass, creates false positives/negatives, and can produce misleading claims that injection has been "detected" or "blocked."

It may be added later as a supplementary signal, but not as a trust oracle.

### C. Disable corrective web search completely

Rejected for this learning pattern because it removes the stale-knowledge correction behavior CRAG is intended to demonstrate.

### D. Allowlist authoritative sources only

Necessary but insufficient. Source authority is not instruction authority, so allowlisting must be combined with instruction/data separation and downstream verification.

## Consequences

### Positive

- The external-search security boundary becomes explicit in code and architecture.
- Non-authoritative search results are rejected deterministically.
- Downstream components can inspect provenance/trust metadata.
- The tutorial can teach the architectural trade-off created by corrective retrieval: freshness improves while the trust surface expands.
- The design avoids claiming that a probabilistic prompt rule is a complete security boundary.

### Negative / Trade-offs

- Restrictive allowlists can reduce recall and may produce safe refusal when useful evidence exists only outside approved sources.
- Source prefixes require governance and maintenance as approved authorities change.
- Allowlisted sites can still contain malicious or compromised content.
- The LLM can still be susceptible to indirect prompt injection despite the prompt boundary.

## Residual Risk

This ADR **does not claim prompt injection is solved**.

Residual risks include:

- malicious content hosted on an approved source;
- compromised authoritative documentation;
- model-specific susceptibility to adversarial instructions;
- prompt injection that survives source restrictions and instruction/data labeling;
- future tool-enabled variants converting a content-integrity problem into an action/authorization problem.

A production system may require additional controls such as content isolation, security classifiers, source reputation/freshness policy, model-specific adversarial evaluation, sandboxed tool execution, least-privilege authorization, and human approval for consequential actions.

## Verification Evidence

Deterministic unit tests verify that:

- non-allowlisted external URLs are rejected;
- lookalike domains are rejected;
- allowlisted documents receive external-source trust metadata;
- adversarial retrieved text remains in the evidence/user message and never becomes a system message;
- the system prompt explicitly denies instruction authority to retrieved content.

These tests verify **architecture invariants**, not universal LLM resistance to prompt injection.

## Architectural Principle

> **Source authority is not instruction authority. Retrieved content may provide evidence, but it must never silently acquire control authority.**
