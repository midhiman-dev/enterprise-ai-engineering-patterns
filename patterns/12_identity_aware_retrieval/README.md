# Pattern 12 — Identity-Aware Retrieval: Authorization-First RAG

**Current maturity:** **DESIGNED**

## Purpose

This pattern studies how an enterprise AI system should preserve user authorization boundaries during retrieval, prompt assembly, and tool execution.

The central engineering rule is:

> **Authentication identifies the caller. Authorization must constrain the retrieval space before evidence reaches the model.**

The reference exercise uses heterogeneous sources with different authorization models:

- SharePoint-style documents with users, groups, inheritance, and unique permissions;
- PostgreSQL structured data protected by row-level or principal-based rules;
- pgvector retrieval with mandatory ACL metadata pre-filtering.

The pattern is intentionally designed as a hands-on security lab rather than a generic RAG tutorial.

## Core Problem

A conventional RAG implementation may retrieve broadly, rank candidates, and remove unauthorized results afterward. This pattern rejects that as the primary security control.

The required flow is:

```text
authenticated caller
  -> validated identity
  -> canonical principals
  -> authorized search space
  -> retrieval / ranking
  -> authorized evidence only
  -> prompt
  -> model
  -> authorized tools
  -> audit evidence
```

The security boundary therefore exists **before model context construction**, not after generation.

## Core Mental Model

```text
JWT / Identity Provider
        |
        v
Validated IdentityContext
(user + tenant + roles + groups + canonical principals)
        |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
SharePoint-style ACL     PostgreSQL rules      pgvector metadata
pre-filter               / RLS pre-filter      pre-filter
        |                      |                      |
        +----------------------+----------------------+
                               |
                               v
                    Authorized evidence only
                               |
                               v
                        Prompt / Model
                               |
                               v
                  Authorized tool execution
                               |
                               v
                      Reconstructible audit
```

## Design Invariants

1. **Identity is resolved once and propagated consistently.** Every retriever and tool receives the same immutable `IdentityContext`.
2. **Authorization happens before retrieval results can become model evidence.** Unauthorized chunks must never enter the context window.
3. **Each source keeps its own authorization semantics.** SharePoint-style ACLs, relational access rules, and vector metadata filters consume the same canonical principal set but enforce access in source-appropriate ways.
4. **The orchestrator does not become a confused deputy.** It must not use a broad privileged identity to retrieve user data and then trim results afterward.
5. **Tools re-authorize independently.** Retrieval authorization does not automatically grant authority to execute an action.
6. **Security is verified with negative tests.** Cross-user tests must prove that restricted content never appears in retrieved chunks or `context_sent`.
7. **Audit evidence reconstructs what the model saw.** The system records caller identity, resolved principals, eligible chunks, retrieved chunks, final context, model response, and tool activity.

## Reference Exercise

The reference lab is local-first and uses:

- Auth0 JWT validation for identity;
- FastAPI for the mock SharePoint service and orchestrator;
- PostgreSQL 16;
- pgvector;
- Docker Compose;
- Python 3.11+.

The design deliberately avoids real enterprise credentials and external mutable systems. SharePoint permissions are simulated through a local service so identity and ACL behavior can be tested repeatedly.

Detailed design: [`TECH_SPEC.md`](TECH_SPEC.md).

## What This Pattern Teaches

### Authentication vs authorization

A valid token proves who the caller is. It does not prove the caller may read every document returned by a retriever.

### Pre-filtering vs post-filtering

Security trimming must define the eligible retrieval set before similarity ranking or prompt assembly. Post-filtering is not the primary security control.

### Identity normalization

Different systems express users, groups, roles, and ownership differently. The application converts validated identity claims into a canonical principal set that source adapters map to their own authorization model.

### Retrieval authorization vs action authorization

An AI system may be allowed to read protected evidence while still lacking permission to execute an action. Tools therefore receive and re-check the same identity context.

### Functional correctness vs security correctness

A useful answer does not prove secure behavior. Security requires explicit negative cases showing that forbidden evidence never crosses the retrieval boundary.

### Auditability

For sensitive enterprise AI, the relevant question is not only "what answer was returned?" but also "what evidence entered the model context, under whose identity, and through which authorization decision?"

## Verification Strategy

The pattern is considered **VERIFIED** only after executable evidence demonstrates that:

- valid and invalid JWT behavior is correct;
- principal resolution is deterministic;
- each retriever applies authorization before returning content;
- cross-user negative tests prevent ACL leakage;
- unauthorized chunks never appear in the final model context;
- tool authorization is independently re-checked;
- audit records can reconstruct the exact context supplied to the model.

Until that evidence exists, the pattern remains **DESIGNED**.

## Relationship to Other Patterns

- **Pattern 01 — Corrective RAG** focuses on retrieval quality, stale evidence, correction, and grounding.
- **Pattern 03 — Tool Calling & MCP** focuses on invoking capabilities through controlled tool boundaries.
- **Pattern 05 — AI Observability** focuses on traces, metrics, and operational visibility.
- **Pattern 07 — Secure & Trustworthy Enterprise AI** provides the broader security context.
- **Pattern 09 — Context, Loop & Harness Engineering** governs runtime context, control loops, permissions, recovery, and audit.
- **Pattern 12 — Identity-Aware Retrieval** focuses specifically on **authorization-preserving retrieval and evidence construction** across heterogeneous data sources.

This pattern remains deliberately narrow: it is not a complete enterprise identity platform and not a general security framework.

## Scope Boundaries

### In scope

- JWT validation;
- immutable identity context;
- canonical users / roles / groups / principals;
- SharePoint-style ACL simulation;
- PostgreSQL RLS or equivalent principal predicates;
- pgvector metadata pre-filtering;
- prompt construction from authorized evidence only;
- tool re-authorization;
- negative security tests;
- reconstructible audit evidence.

### Out of scope for the first implementation

- real SharePoint / Microsoft Graph / Entra ID integration;
- production secrets management;
- production-scale multi-tenancy;
- advanced relationship-based authorization engines such as OpenFGA or SpiceDB;
- external systems capable of real mutations;
- high-availability or multi-region deployment.

## Pattern Status Rule

The design is complete enough to guide implementation, so the pattern is **DESIGNED**.

It must not be presented as **BUILDING** until implementation begins, and it must not be presented as **VERIFIED** until negative authorization tests and audit evidence exist.
