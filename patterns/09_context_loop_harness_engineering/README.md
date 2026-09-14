# Pattern 09 — Advanced AI Engineering: Context, Loop & Harness

**Current maturity:** **DESIGNED**

## Purpose

This pattern studies the engineering environment around AI systems rather than treating the model itself as the architecture.

It combines three related tracks:

1. **Context Engineering** — control what information the model receives.
2. **Loop Engineering** — control how an AI workflow makes progress, retries, verifies, and stops.
3. **Harness Engineering** — control tools, permissions, policy, evaluation, governance, human approval, observability, and audit.

The central engineering question is:

> **How do we engineer the runtime around an AI model so it receives the right context, operates through bounded and recoverable loops, and executes inside a governed, observable, and testable harness?**

The learning scaffold for this pattern uses a consistent four-layer structure:

- `tutorial/` — plain-English explanation + mental model;
- `demo/` — small runnable example isolating one idea;
- `enterprise/` — architecture, controls, trade-offs, failure handling, evaluation, governance;
- `adrs/` — Architecture Decision Records suitable for durable portfolio evidence.

The source tutorial package is treated as a starting point. It does not by itself make this pattern VERIFIED.

---

# Track 1 — Context Engineering

## Core question

> **What should the model see right now, and how do we control that context deliberately?**

Primary mental model:

> **Write → Select → Compress → Isolate**

### Learning goals

Understand and implement:

- writing large or durable context out of the immediate prompt;
- selecting only relevant context back in;
- compressing/summarizing context when useful;
- isolating task/sub-agent contexts;
- token-budget awareness;
- stale-context handling;
- context provenance;
- context leakage prevention;
- context quality evaluation.

### Enterprise direction

Reference design:

> **Research-agent context pipeline with token budgets, trajectory store, context-selection policy, sub-agent isolation, and evaluation gates.**

### Failure modes to exercise

- context-window overflow;
- stale context;
- irrelevant context flooding;
- cross-task leakage;
- oversized tool output;
- missing critical context;
- over-compression that removes necessary evidence;
- repeated invariant context causing unnecessary token cost.

### Interview recall anchor

> **Context is a budgeted engineering resource, not an unlimited prompt buffer.**

---

# Track 2 — Loop Engineering

## Core question

> **How does an AI system make progress without looping forever, repeating unsafe actions, or falsely claiming success?**

Primary mental model:

> **Observe → Reason → Act → Verify**

### Learning goals

Understand and implement:

- controller-owned iteration;
- deterministic verification/oracles where possible;
- explicit stop conditions;
- hard max-step limits;
- bounded retries;
- transient vs permanent failure classification;
- no-progress detection;
- safe recovery;
- idempotency;
- human escalation;
- timeout handling.

### Important rule

> **The model reasons inside the loop. Code owns the loop.**

### Enterprise direction

Reference design:

> **Controller-owned loop with explicit state, stop rules, bounded recovery, verification gates, escalation, and observable trajectory.**

### Failure modes to exercise

- transient tool failure;
- repeated verification failure;
- infinite/no-progress loop;
- ambiguous tool result;
- repeated side effect;
- stale loop state;
- max-step exhaustion;
- human escalation timeout.

### Interview recall anchor

> **A production loop must have a deterministic owner, explicit termination, verification, and recovery semantics.**

---

# Track 3 — Harness Engineering

## Core question

> **What surrounds the model so its capabilities can be used safely and reliably in an enterprise?**

### Learning goals

Understand and implement:

- typed tool interfaces;
- tool gateway;
- allow/deny policies;
- argument-level authorization;
- task-scoped identity;
- least privilege;
- approval gates;
- sandboxing / execution boundaries;
- audit trail;
- evaluation gates;
- governance;
- observability;
- monitoring;
- release gates;
- cost/budget controls.

### Enterprise direction

Reference design:

> **Tool gateway + policy-as-code + task-scoped identity + human approval + evaluation gates + immutable audit evidence.**

### Failure modes to exercise

- unauthorized tool access;
- valid tool with forbidden arguments;
- privilege escalation attempt;
- expired/scoped credential;
- missing human approval;
- approval rejection/timeout;
- policy misconfiguration;
- audit gap;
- unsafe retry;
- model/tool mismatch.

### Interview recall anchor

> **The model is not the architecture. The harness makes the model usable.**

---

# How the Three Tracks Fit Together

```text
                HARNESS
 ┌──────────────────────────────────┐
 │ Identity · Tools · Policy        │
 │ Governance · Evals · HITL        │
 │ Observability · Budgets · Audit  │
 │                                  │
 │          LOOP                    │
 │   ┌──────────────────────────┐   │
 │   │ Observe                  │   │
 │   │ Reason                   │   │
 │   │ Act                      │   │
 │   │ Verify                   │   │
 │   │ Stop / Recover           │   │
 │   │                          │   │
 │   │       CONTEXT            │   │
 │   │  ┌───────────────────┐   │   │
 │   │  │ Write             │   │   │
 │   │  │ Select            │   │   │
 │   │  │ Compress          │   │   │
 │   │  │ Isolate           │   │   │
 │   │  └───────────────────┘   │   │
 │   └──────────────────────────┘   │
 └──────────────────────────────────┘
                 │
          Foundation Model
```

Interpretation:

- **Context Engineering** controls what the model knows for the current task.
- **Loop Engineering** controls how the system iterates toward an outcome.
- **Harness Engineering** controls what the system is allowed to do and how it is governed, observed, evaluated, and stopped.

---

# Relationship to Other Patterns

Pattern 09 is an **integration pattern** rather than a duplicate of existing topics.

It may consume capabilities from other patterns:

- observability;
- evaluation;
- security;
- provider abstraction;
- governance;
- state/recovery.

Its distinct concern is:

> **How those capabilities compose into the runtime engineering environment around AI/agent systems.**

Pattern 10 complements Pattern 09:

- **Pattern 09** protects and governs the AI runtime.
- **Pattern 10** keeps the business domain authoritative.

Conceptually:

```text
AI Harness
Context / Loop / Policy
        │
        ▼
AI proposal
        │
        ▼
Application boundary
        │
        ▼
DDD Domain Core
Aggregates / Invariants / Events
```

---

# Learning Structure

Each track should retain the same four layers.

## tutorial/

Plain-English explanation and mental model.

## demo/

Small runnable example isolating one engineering idea.

The supplied demos intentionally use stubs for model behaviour so engineering surfaces remain visible.

## enterprise/

Production-oriented architecture including:

- controls;
- trade-offs;
- failure handling;
- evaluation;
- governance;
- observability;
- recovery.

## adrs/

Architecture Decision Records that preserve:

- decision;
- alternatives;
- rationale;
- consequences;
- deferred work.

Supporting material may include:

- learning path;
- glossary;
- portfolio guide;
- ADR templates;
- evaluation rubric templates;
- shared diagrams.

---

# Learning Method

The existing tutorial/demo is only the starting point.

For each track use:

> **LEARN → RUN → MODIFY → BREAK → OBSERVE → FIX → PROVE → EXPLAIN → OWN**

Examples:

### Context Engineering

- deliberately overflow the context budget;
- inject stale context;
- inject irrelevant context;
- compare full-context vs selective-context token cost;
- test isolation between tasks/sub-agents.

### Loop Engineering

- make a tool fail transiently;
- force repeated verification failure;
- create a no-progress loop;
- test hard max-step termination;
- simulate ambiguous side effects and safe recovery.

### Harness Engineering

- call a forbidden tool;
- manipulate allowed-tool arguments beyond authority;
- expire task-scoped credentials;
- reject/timeout approval;
- prove that audit evidence reconstructs the decision/action.

---

# Verification Criteria

Pattern 09 should not move to VERIFIED merely because the source demos run.

Executable evidence should show that:

## Context

- context budgets are enforced;
- irrelevant/stale context can be excluded;
- isolation boundaries work;
- context choices can be inspected;
- cost/quality trade-offs can be measured.

## Loop

- max-step limits stop runaway loops;
- transient failures recover within policy;
- permanent failures do not retry indefinitely;
- verification controls terminal success;
- unsafe duplicate effects are prevented;
- escalation occurs when recovery limits are exhausted.

## Harness

- unauthorized tools/actions are blocked;
- approval gates are enforced;
- task-scoped authority is demonstrable;
- every important decision/action is auditable;
- eval/release gates can stop unsafe changes;
- monitoring/observability support operator diagnosis.

---

# Cross-Cutting Production Concerns

This pattern must explicitly exercise:

> **Governance → Observability → Monitoring**

## Governance

Use:

> **Policy → Enforcement Point → Owner → Evidence**

## Observability

Capture enough evidence to reconstruct:

- context selected;
- loop step;
- model/provider;
- tool call;
- policy decision;
- approval;
- verification result;
- stop/recovery decision;
- token/cost/latency;
- terminal outcome.

## Monitoring

Establish signals such as:

- loop rate;
- max-step exhaustion;
- tool failure rate;
- policy-denial rate;
- approval wait time;
- context-budget pressure;
- token/cost trend;
- repeated recovery;
- evaluation regressions.

---

# Interview Recall Framework

If asked what advanced AI engineering means beyond prompts/models:

> **Context → Loop → Harness**

### Context

What information should the model receive for this task?

### Loop

How does the system make progress, verify results, recover, and stop?

### Harness

What tools, permissions, policies, evaluations, controls, and human authority surround execution?

Compact answer:

> “I separate three engineering concerns. Context Engineering controls what information enters the model and within what budget. Loop Engineering keeps iterative execution bounded, verified, and recoverable. Harness Engineering governs tools, permissions, human approvals, evaluation, observability, and audit. The model reasons inside those boundaries rather than owning them.”

---

# Scope Boundary

This pattern is not:

- a framework comparison;
- a multi-agent showcase;
- a prompt-engineering tutorial;
- an excuse to introduce more orchestration technology;
- a claim that autonomous agents should replace deterministic workflows.

The engineering surfaces remain the focus.

Prefer standard-library/fake-model demos where that makes state, policy, failure, and verification easier to inspect.

Introduce external frameworks only when they add a distinct learning objective.

---

# Maturity Rationale

Current maturity is **DESIGNED** because:

- the three-track structure exists;
- tutorial/demo/enterprise/ADR scaffolding exists;
- runnable demonstration concepts exist;
- enterprise controls and failure modes have been identified.

The pattern remains below VERIFIED until the exercises are personally worked through, modified, broken, observed, and supported by executable evidence under this repository's maturity rules.
