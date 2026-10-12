# Pattern 13 — Decision-Native AI Architecture: Probabilistic Judgement, Deterministic Authority

**Current maturity:** **DESIGNED**  
**Portfolio reference lab:** [Governed Intake Router](https://github.com/midhiman-dev/portfolio-knowledge-base/blob/main/projects/governed-intake-router-jev.md) (design only; no benchmark results yet)

## Purpose

Study when and how a bounded probabilistic model can make semantic judgements inside a workflow without acquiring business authority.

> **Model judges; code governs.**

A probability is evidence about a proposed classification, **not** permission to execute an action. The application owns authorization, domain invariants, policy precedence, threshold decisions, human escalation, and auditing.

## Enterprise problem

A service ticket may need a queue, urgency, sensitivity, suspected injection and human-review assessment. A generative LLM can return a JSON classification, but that does not automatically make its confidence meaningful, its outputs stable, or its suggested actions authorized. Rules-only approaches may be brittle on ambiguous free text.

The architecture needs a testable separation between **uncertain semantic judgement** and **deterministic permitted action**.

## Core mental model

```text
Untrusted request + verified context
             |
             v
Deterministic input validation, privacy minimization, authorization
             |
             v
Typed decision request (Choice / ordinal Score / binary judgement)
             |
             v
Replaceable model or classifier adapter
             |
             v
Normalized judgement + provenance + probability semantics
             |
             v
Calibration, thresholds, abstention, quality/availability checks
             |
             v
Deterministic policy + domain rules + permission checks
             |
      +------+------+----------------+
      |             |                |
   permitted      human           restrict/
   action         review          quarantine
      |             |                |
      +-------------+----------------+
                    |
              Decision audit
```

## Design invariants

1. **No model directly authorizes business operations.** Typed inference output is data, never a command to execute.
2. **Output domains are explicit.** Choices, ordinal levels and binary labels are versioned; arbitrary model-generated strings cannot silently enter policy.
3. **Probabilities are not universal confidence.** Native probability distributions, externally calibrated scores and generative LLM self-reported confidence must be distinguished.
4. **Abstention is a valid outcome.** Low confidence, ambiguity, missing probabilities, unsupported outputs or unavailable providers route to a safe human-controlled state.
5. **Policy has deterministic precedence.** Sensitive cases, suspected manipulation and domain invariants cannot be bypassed by a high queue score.
6. **Authority is checked independently.** Identity, permissions, risk classification and human approval remain enforceable regardless of model choice.
7. **Adapters are replaceable.** A model switch never requires rewriting the business policy.
8. **Quality is measured at automation coverage.** Report correctness of automatically handled cases *and* how much work was actually automated.
9. **Failure is tested.** Malformed distributions, unavailable models, timeout, drift, reordered choices and adversarial language have explicit tests.
10. **Audit is reconstructible and privacy-aware.** Store model/revision, question and policy versions, sanitized input hash, judgement, selected policy rule, action and human override without leaking sensitive data.

## Where the pattern applies

- Service desk and HR/finance intake routing
- Model/tool/agent selection under cost and authority constraints
- Document or exception triage
- Risk signals feeding deterministic review workflows
- Evaluation and approval checkpoints in agentic systems

**Do not use it by default** for fully deterministic classification, a stable supervised classifier with superior measured TCO/quality, an open-ended reasoning/generation problem, or decisions where probabilities cannot be validated and abstention is impossible.

## Relationship to existing patterns

- **Pattern 04 — LLM Gateway & Model Routing:** chooses execution providers; Pattern 13 governs the uncertainty and authority of the decision that may drive that choice.
- **Pattern 06 — AI System Evaluation:** supplies golden data, calibration, evaluation and regression methods; Pattern 13 applies them to consequential decision handoffs.
- **Pattern 07 — Secure & Trustworthy Enterprise AI:** contributes privacy, input trust and authorization guardrails.
- **Pattern 10 — Domain-Driven AI Architecture:** owns domain invariants and authoritative state transitions; Pattern 13 defines the earlier probabilistic judgement-to-policy boundary.
- **Pattern 12 — Identity-Aware Retrieval:** constrains access to evidence before model inference; Pattern 13 prevents inference from bypassing action authority.

## Reference lab — Governed Intake Router

The existing [Governed Intake Router](https://github.com/midhiman-dev/portfolio-knowledge-base/blob/main/projects/governed-intake-router-jev.md) is the **consuming portfolio lab**, not a duplicate project in this repository. It plans one common five-question contract and four adapters:

| Candidate | Architectural dimension |
|---|---|
| Jev | Managed bounded decision inference |
| Vela 2.0 | Open-weight / self-hosted bounded decision inference |
| Microsoft-Decision-1 | Managed enterprise-platform decision inference |
| Conventional LLM | Generative structured-output baseline |

Its detailed [technical specification](https://github.com/midhiman-dev/portfolio-knowledge-base/blob/main/projects/governed-intake-router-jev/TECH_SPEC.md), [build plan](https://github.com/midhiman-dev/portfolio-knowledge-base/blob/main/projects/governed-intake-router-jev/BUILD_PLAN.md) and [ADR](https://github.com/midhiman-dev/portfolio-knowledge-base/blob/main/projects/governed-intake-router-jev/ADR-001-JEV-DECISION.md) remain canonical in the portfolio knowledge base. Any provider claim is a hypothesis until independently evaluated.

## Proposed learning layers

- **Tutorial:** probability vs confidence, calibration, selective classification, abstention and judgement/authority boundaries.
- **Demo:** small runnable fake-adapter pipeline with deterministic policy, synthetic tickets and fault injection. Do not require paid model access for core tests.
- **Enterprise:** link to the actual Governed Intake Router implementation and its measured comparisons when they exist.
- **ADRs:** record decision-native vs rules/classical ML/LLM trade-offs; avoid copying full project ADRs here.

These are **planned learning assets**, not already-implemented folders.

## Verification gates

The pattern becomes **BUILDING** only when a runnable demonstration starts. It becomes **VERIFIED** only with executable evidence of:

- provider-neutral conformance on typed decisions;
- deterministic policy regardless of provider and no actions on malformed/failed judgements;
- explicit abstention/human fallback and authorization checks;
- measured calibration/reliability and accuracy at coverage on held-out examples;
- perturbation tests for paraphrase, option order and malformed inputs;
- recorded model/question/policy versions, decision traces and reproducible test commands;
- honestly reported limits, rare-event sample sizes and trade-offs.

The reference lab's 300-ticket dataset is a bounded learning baseline; it is **not sufficient to certify production safety for rare sensitive/security misses**.

## Scope and status

**In scope:** design contracts, calibration/abstention, deterministic policy, alternative model implementations, audit and verification.

**Out of scope initially:** production ticketing integration, SSO, large-scale deployment, real HR/PII records, autonomous actions and vendor-specific performance claims.

**Status: DESIGNED.** This repository entry documents the architecture and proof plan. No implementation or comparison evidence is claimed.

Detailed design: [TECH_SPEC.md](TECH_SPEC.md).
