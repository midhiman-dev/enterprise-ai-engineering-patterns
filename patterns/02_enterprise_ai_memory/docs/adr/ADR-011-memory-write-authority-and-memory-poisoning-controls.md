# ADR-011 — Persistent Memory Write Authority and Memory Poisoning Controls

## Status

Accepted

## Context

Pattern 02 introduces working, episodic, semantic, and procedural memory for an enterprise HR assistant. Once memory persists across sessions, untrusted content can become dangerous if it is stored without preserving provenance, ownership, authority, or verification state.

Examples include:

- an employee asking the assistant to "remember" a new leave policy for everyone;
- a user assertion such as "my manager approved this" being stored and later treated as verified fact;
- prompt-injection text attempting to persist itself as a procedure;
- one employee influencing another employee's context through an unauthorized shared write.

The existing Pattern 02 principle already distinguishes AI memory from enterprise truth. That distinction must also be enforced at the point where memory is written and later retrieved.

## Decision

Persistent AI memory will be governed by deterministic write authorization, provenance, trust metadata, and retrieval-time authority checks.

User or retrieved content cannot directly mutate shared semantic or procedural memory.

The architecture will introduce an explicit memory-write policy boundary, conceptually represented by `MemoryWritePolicy`, with supporting provenance/trust metadata.

Baseline rules include:

```text
employee conversation
→ working memory allowed
→ employee-scoped episodic memory allowed where appropriate
→ shared semantic-memory write denied
→ procedural-memory write denied

user assertion about approval, payroll, entitlement, or case state
→ may be retained as unverified historical context
→ must not become authoritative enterprise state

approved HR policy-ingestion workflow
→ may create candidate semantic-memory versions
→ source validation, evaluation, and activation still required

approved procedure deployment
→ may create/version procedural memory
→ explicit approval/version activation required
```

Persistent memory records should carry enough metadata to reconstruct origin and authority, including where appropriate:

```text
source_type
source_id
subject_id
created_by
authority_level
verification_status
trust_classification
retention_policy
```

Retrieval must apply scope, authority/trust, and freshness checks before memory enters LLM context.

## Alternatives Considered

### 1. Let the LLM decide what should be remembered

Rejected because model judgment is probabilistic and can be manipulated by user or retrieved content. It also allows authority escalation without a deterministic control boundary.

### 2. Persist everything but instruct the model not to trust unverified memories

Rejected because untrusted content would already have crossed the persistence boundary and could continue influencing future contexts. Prompt guidance is not an adequate authorization mechanism.

### 3. Allow users to update semantic memory with later human cleanup

Rejected because incorrect shared memory could affect other employees before review and creates an unnecessary remediation burden.

### 4. Block all episodic persistence from user conversations

Rejected because cross-session continuity is a legitimate Pattern 02 capability. The safer design is to preserve provenance and authority rather than discard useful historical context entirely.

## Consequences

### Positive

- untrusted conversation content cannot silently become organizational truth;
- semantic and procedural memory have explicit write-authority boundaries;
- user assertions can remain useful without being misrepresented as verified facts;
- cross-user poisoning risk is reduced;
- memory behaviour becomes more auditable and testable;
- poisoning failures can be represented as deterministic regression cases.

### Costs / Trade-offs

- persistent memory records require additional metadata;
- memory writes become more explicit and may require additional workflow logic;
- context construction must account for trust/authority, not only relevance;
- some memory updates may require verification or administrative workflows;
- developers must distinguish "remembered user statement" from "verified enterprise fact."

## Risks

A deterministic policy can still be incorrectly configured or implemented.

Mitigations include:

- zero-tolerance tests for unauthorized semantic/procedural writes;
- cross-user isolation tests;
- provenance completeness checks;
- production telemetry for rejected/allowed memory writes;
- versioned policy configuration;
- Pattern 06 regression coverage for known poisoning attempts.

This ADR does not claim to solve all prompt injection or adversarial-model behaviour. It governs the authority transition into persistent memory.

## Cross-Pattern Connection

```text
Pattern 01 — Corrective RAG
Retrieved evidence is data, not instruction authority.
        ↓
Pattern 02 — Enterprise AI Memory
Untrusted content cannot gain persistent memory authority.
        ↓
Pattern 05 — AI Observability
Observe memory-write, scope, rejection, trust, and retrieval behaviour in production.
        ↓
Pattern 06 — AI System Evaluation
Known poisoning attempts and production failures become permanent regression cases.
```

Pattern 02 owns the runtime memory trust boundary. Pattern 05 provides production visibility into that boundary. Pattern 06 verifies that changes do not weaken it before release.

## Evidence Required During Implementation

The implementation should eventually demonstrate:

```text
unauthorized semantic-memory writes = 0
unauthorized procedural-memory writes = 0
unauthorized cross-user propagation = 0
unverified assertions returned as authoritative facts = 0
```

Golden Scenario 6 — Persistent Memory Poisoning Attempt — will be added to the Pattern 02 test/evaluation suite.

## Revisit Conditions

Revisit this ADR if:

- new memory classes with different authority semantics are introduced;
- users are intentionally permitted to contribute shared organizational knowledge;
- semantic/procedural memory moves to a workflow with external approval/governance infrastructure;
- memory provenance requirements become insufficient for audit or compliance needs;
- evaluation evidence shows the current deterministic policy is too coarse or misses important attack paths.
