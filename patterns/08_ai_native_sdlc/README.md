# Pattern 08 — AI-Native SDLC: Human-Governed AI-Assisted Engineering

**Maturity:** IDENTIFIED  
**Status:** Initial direction captured; implementation not started  
**Last updated:** 2026-09-11

## Purpose

This pattern demonstrates an AI-Native SDLC where AI agents accelerate engineering stages, but every consequential handoff is represented by a versioned repository artifact that is reviewed and explicitly approved by a human before downstream agents consume it.

The reference scenario will use a small clean-room REXX/CMD-style monolithic modernization exercise.

## Core lifecycle

~~~text
REXX / CMD Script
        ↓
AI Analysis Agent
        ↓
legacy-analysis-v0.1.md
        ↓
HITL Business Validation
        ↓
legacy-analysis-approved-v1.0.md
        ↓
AI Design Agent
        ↓
modernization-design-v0.1.md
        ↓
HITL Architecture Review
        ↓
modernization-design-approved-v1.0.md
        ↓
AI Implementation Agent — Planning
        ↓
implementation-plan-v0.1.md
        ↓
HITL Implementation Plan Review
        ↓
implementation-plan-approved-v1.0.md
        ↓
AI Implementation Agent — Execution
        ↓
Source Code + Generated Tests
+ implementation-report-v0.1.md
        ↓
HITL Technical Review
        ↓
implementation-review-approved-v1.0.md
        ↓
Testing & Validation
        ↓
validation-report-v0.1.md
        ↓
HITL Functional Approval
        ↓
validation-report-approved-v1.0.md
        ↓
Production Readiness Agent
        ↓
release-readiness-v0.1.md
        ↓
HITL Release Approval
        ↓
release-readiness-approved-v1.0.md
        ↓
RELEASE
~~~

## Central control rule

> **A downstream AI agent may consume only the latest approved upstream artifact, never an unapproved draft artifact.**

Examples:

- Design consumes legacy-analysis-approved-v1.0.md, not the draft.
- Implementation planning consumes modernization-design-approved-v1.0.md.
- Code generation consumes implementation-plan-approved-v1.0.md.
- Production Readiness consumes approved implementation and validation evidence.

This prevents an AI misunderstanding from silently propagating through the lifecycle.

## Artifact convention

Draft artifacts remain explicit and are preserved in Git:

- legacy-analysis-v0.1.md
- modernization-design-v0.1.md
- implementation-plan-v0.1.md
- implementation-report-v0.1.md
- validation-report-v0.1.md
- release-readiness-v0.1.md

Human-approved baselines are also explicit:

- legacy-analysis-approved-v1.0.md
- modernization-design-approved-v1.0.md
- implementation-plan-approved-v1.0.md
- implementation-review-approved-v1.0.md
- validation-report-approved-v1.0.md
- release-readiness-approved-v1.0.md

Source code and tests remain Git-versioned engineering artifacts rather than copied into artificial version folders.

## Stage 1 — AI Analysis Agent

Produces legacy-analysis-v0.1.md containing:

- program purpose and execution flow;
- parameters/defaults;
- business rules;
- database reads/writes;
- file/command dependencies;
- external interfaces;
- outputs;
- error/return-code handling;
- assumptions and unresolved questions.

### HITL Business Validation

Produces legacy-analysis-approved-v1.0.md with corrections, accepted interpretations, and unresolved items.

## Stage 2 — AI Design Agent

Consumes only the approved analysis and produces modernization-design-v0.1.md covering:

- target .NET structure;
- parameter/configuration mapping;
- database/data-access mapping;
- component boundaries;
- integration handling;
- logging and exception strategy;
- security considerations;
- intentional behaviour changes.

### HITL Architecture Review

Produces modernization-design-approved-v1.0.md.

## Stage 3 — AI Implementation Agent: Planning

Before generating source code, the agent produces implementation-plan-v0.1.md covering:

- projects/files to create or modify;
- implementation sequence;
- design-requirement-to-code mapping;
- classes/components to introduce;
- database/integration changes;
- configuration changes;
- tests to create;
- build/test commands;
- dependencies and assumptions;
- protected areas that must not change;
- completion criteria.

### HITL Implementation Plan Review

Produces implementation-plan-approved-v1.0.md.

This gate catches architecture or scope mistakes before large amounts of code are generated.

## Stage 4 — AI Implementation Agent: Execution

Consumes only the approved implementation plan.

Produces:

- source code;
- generated tests;
- configuration/build changes;
- implementation-report-v0.1.md.

The report records approved inputs, files changed, requirements implemented, tests generated, build result, deviations/assumptions, and Git commit/reference where available.

### HITL Technical Review

Produces implementation-review-approved-v1.0.md and checks:

- implementation follows approved design and plan;
- code quality and maintainability;
- business-rule correctness;
- error handling and logging;
- security;
- database/integration behaviour;
- test quality;
- unnecessary complexity.

## Stage 5 — Testing & Validation

Produces validation-report-v0.1.md.

Checks may include unit, integration, functional, and regression tests; input/output comparison; database-result validation; error-path validation; and legacy-versus-modern comparison where practical.

### HITL Functional Approval

Produces validation-report-approved-v1.0.md confirming the expected business outcome and accepted intentional differences.

## Stage 6 — Production Readiness Agent

The Production Readiness Agent does not re-test business logic. Its job begins after technical and functional validation.

It checks whether the approved application is operationally ready to **deploy, operate, support, observe, and recover**.

It produces release-readiness-v0.1.md.

### Production readiness checks

**Build and package**
- release build succeeds;
- deployable package is complete;
- runtime dependencies are identified;
- version/build identity is recorded.

**Environment and configuration**
- environment-specific settings are documented;
- endpoints, paths, parameters, and external dependencies are identified;
- secrets use the approved mechanism rather than being embedded;
- required prerequisites are known.

**Deployment**
- deployment steps and order are documented;
- prerequisites are clear;
- upgrade/migration steps are defined where relevant;
- deployment health checks are defined.

**Logging and monitoring**
- useful application logs are available;
- important failures are observable;
- health/availability checks are defined where applicable;
- monitoring/alerting expectations are documented.

**Security and access**
- service/runtime identities are understood;
- required permissions are documented;
- credentials handling and access boundaries are reviewed;
- no release-blocking security issue remains unresolved.

**Supportability**
- runbook/support documentation exists;
- known issues and operational limitations are recorded;
- ownership/escalation path is clear;
- common recovery actions are documented.

**Rollback/fallback**
- rollback or fallback approach is defined;
- previous stable version/recovery path is understood;
- rollback impact is documented where necessary.

**Evidence completeness**
- approved legacy analysis exists;
- approved modernization design exists;
- approved implementation plan exists;
- technical review approval exists;
- functional validation approval exists;
- required test evidence is available.

> **Testing asks: “Does the application work?” Production Readiness asks: “Can we deploy, operate, support, observe, and recover it safely?”**

The agent compiles readiness evidence and identifies gaps. It does not make the final release decision.

### HITL Release Approval

Human release/operations/application owners review release-readiness-v0.1.md.

If accepted, the baseline becomes release-readiness-approved-v1.0.md.

The human gate owns the final release decision and any consciously accepted residual risk.

## Reusable AI-Native SDLC pattern

Engineering view:

> **Analyze → Validate → Design → Review → Plan → Review → Implement → Review → Test → Approve → Release**

AI-native governance view:

> **Generate → Version → Review → Correct → Approve → Promote → Consume**

The second line is the core reusable pattern.

## Failure experiment

The public exercise should deliberately include at least one incorrect AI interpretation in a draft artifact and show the HITL correction before the next agent runs.

Example: the AI incorrectly interprets a REXX return code in legacy-analysis-v0.1.md; human review corrects it in legacy-analysis-approved-v1.0.md. The downstream Design Agent receives only the approved version.

This proves why the gate exists: without it, a bad analysis can propagate into design, implementation, tests, and release evidence.

## Planned repository structure

~~~text
patterns/
└── 08_ai_native_sdlc/
    ├── README.md
    ├── legacy/
    ├── artifacts/
    │   ├── analysis/
    │   ├── design/
    │   ├── implementation/
    │   ├── validation/
    │   └── release/
    ├── modernized/
    ├── tests/
    └── evidence/
        └── lifecycle-trace.md
~~~

## Claim boundary

This public pattern is a clean-room engineering demonstration inspired by real modernization experience. It must not imply that the full Pattern 08 artifact/governance framework existed by this exact name or structure during the original professional REXX engagement.
