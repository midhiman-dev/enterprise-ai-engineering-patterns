# TECH_SPEC.md
## Pattern 12 — Identity-Aware Retrieval: Authorization-First RAG

**Version:** 1.0  
**Status:** Final Design  
**Pattern maturity:** DESIGNED  
**Last updated:** 2026-10-02

## 1. Purpose

Build a local, repeatable hands-on laboratory that demonstrates **identity-aware retrieval** for secure enterprise AI systems.

The lab must make authorization behavior visible and testable across the complete evidence path:

- who is making the request;
- which principals represent that caller;
- which source records or chunks are eligible;
- which evidence is retrieved and ranked;
- what context is sent to the model;
- which tools may execute;
- what audit evidence remains afterward.

The lab is a reference implementation for the pattern. It is not a production identity platform.

## 2. Architectural Problem

Enterprise AI systems frequently retrieve information from sources with different identity and authorization models: document repositories using ACLs, relational databases using ownership or row-level rules, and vector stores that may have no native enterprise authorization model.

A naive implementation may retrieve broadly and remove unauthorized results afterward. This design rejects that approach.

> **Authorization must constrain the eligible retrieval set before content can participate in ranking, prompt assembly, or model inference.**

Target path:

```text
Authenticate
  -> Resolve IdentityContext
  -> Map canonical principals
  -> Apply source-specific authorization
  -> Retrieve / rank authorized evidence
  -> Assemble context
  -> Invoke model
  -> Re-authorize tools
  -> Record audit evidence
```

## 3. Goals and Success Criteria

| Goal | Success criterion |
|---|---|
| Identity is the control plane | Every retriever and tool receives a verified, immutable `IdentityContext` derived from a validated JWT. |
| Authorization precedes ranking | Unauthorized content is excluded before it can become candidate model evidence. |
| No context leakage | Negative tests prove that unauthorized chunks never appear in `context_sent`. |
| Source fidelity | Each source uses an authorization mechanism appropriate to its own model. |
| Consistent principal semantics | All adapters consume the same canonical principal set and map it locally. |
| Tool authority remains explicit | Tools re-check the same identity context before returning protected data or simulating an action. |
| Audit completeness | A request can be reconstructed from caller identity through eligible evidence, retrieved evidence, context, model output, and tools invoked. |
| Learning clarity | The identity and authorization flow can be traced from code and tests without hidden framework behavior. |

## 4. Scope

### 4.1 In scope

- Auth0 JWT validation using a free tenant;
- custom claims for roles, groups, and tenant;
- canonical principal resolution;
- a local Mock SharePoint service;
- SharePoint-style users, groups, inheritance, and unique permissions;
- PostgreSQL structured data;
- PostgreSQL RLS or equivalent explicit principal predicates;
- pgvector similarity retrieval with mandatory authorization metadata filters;
- authorized prompt assembly;
- simulated tools that re-authorize the caller;
- audit evidence for the lab;
- Docker Compose for local dependencies;
- negative authorization tests.

### 4.2 Out of scope

- real Microsoft SharePoint;
- Microsoft Graph;
- Entra ID integration;
- real SQL Server;
- production secrets management;
- production high availability or multi-region deployment;
- external systems capable of real mutations;
- advanced ReBAC engines such as OpenFGA or SpiceDB;
- production-scale multi-tenant isolation.

### 4.3 Non-goals

- maximizing retrieval quality;
- benchmarking vector-store performance;
- building a full enterprise IAM solution;
- building a generalized authorization framework;
- building a production SaaS platform.

## 5. Key Design Invariants

### 5.1 Identity is resolved once

The API boundary validates the JWT and creates an immutable `IdentityContext`. Retrievers and tools do not independently reinterpret raw token claims.

### 5.2 Canonical principals are the shared security contract

The identity context includes normalized principals such as:

```text
user:alice@company.com
group:hr-managers
role:compensation-reader
tenant:company-a
```

Each source adapter maps those principals to its own authorization mechanism.

### 5.3 Authorization happens before model evidence exists

Unauthorized content must not enter candidate chunks returned to orchestration, prompt assembly, model input, or protected tool output.

### 5.4 The orchestrator must not become a confused deputy

The orchestrator must not retrieve all user data using a broad privileged service identity and rely on post-processing to remove restricted content.

### 5.5 Tool authorization is independent

Retrieval authority does not automatically imply action authority. A tool must receive the caller's `IdentityContext` and independently validate its own authorization rule.

### 5.6 Security claims require negative evidence

It is not enough to prove that an authorized user can retrieve a document. The implementation must also prove that another user cannot retrieve or inject that document into model context.

### 5.7 Audit records describe evidence flow

For every query, the system must be able to reconstruct caller, resolved principals, eligible evidence, retrieved evidence, exact context sent, model response, and tools invoked.

The audit trail is evidence for the lab, not a claim of production compliance.

## 6. High-Level Architecture

```text
Client
  |
  | JWT
  v
API / FastAPI Orchestrator
  |
  +--> JWT validation
  +--> immutable IdentityContext
  |
  +----------------------+----------------------+----------------------+
  |                      |                      |
  v                      v                      v
Mock SharePoint       PostgreSQL             pgvector
ACL adapter           structured adapter      vector adapter
  |                      |                      |
  | ACL pre-filter       | RLS / predicate     | metadata pre-filter
  +----------------------+----------------------+----------------------+
                               |
                               v
                    Authorized evidence only
                               |
                               v
                      Prompt assembly
                               |
                               v
                          Model call
                               |
                               v
                     Authorized tool(s)
                               |
                               v
                         Audit record
```

## 7. Identity Model

### 7.1 IdentityContext

The application uses one immutable security context for the entire request.

Conceptual model:

```python
IdentityContext(
    user_id: str,
    email: str,
    tenant_id: str | None,
    roles: tuple[str, ...],
    groups: tuple[str, ...],
    principals: tuple[str, ...],
)
```

The exact implementation may use an immutable dataclass or another simple typed structure.

### 7.2 Principal normalization

Principal values should be canonical and explicit:

```text
user:alice@company.com
group:hr-managers
role:hr-reader
tenant:company-a
```

Adapters must not depend directly on provider-specific raw claim names once `IdentityContext` exists.

### 7.3 Authentication boundary

The API layer validates signature, issuer, audience, expiry, and required claims. Only after token validation succeeds may the application construct `IdentityContext`.

## 8. Source-Specific Authorization Strategies

| Source | Identity model | Authorization mechanism |
|---|---|---|
| Mock SharePoint | users, groups, inheritance, unique permissions, sensitivity metadata | live ACL lookup and/or stored ACL metadata followed by principal intersection |
| PostgreSQL structured data | row ownership, department/group/tenant constraints | RLS using request-local principal context, or explicit parameterized predicates |
| pgvector | vector similarity plus stored ACL metadata | mandatory ACL metadata predicate in the same query that performs similarity ranking |

The adapters share the same identity input, but they do **not** share one generic authorization implementation. Source fidelity matters more than forcing every source into one artificial authorization abstraction.

## 9. Retrieval Contract

A retriever must require identity.

```python
class IdentityAwareRetriever(ABC):
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        identity: IdentityContext,
        top_k: int,
    ) -> list[AuthorizedEvidence]:
        ...
```

A retriever must never expose a protected retrieval path that omits identity.

Required behavior:

1. accept validated `IdentityContext`;
2. derive source-specific authorization constraints;
3. query only eligible records/chunks;
4. rank only authorized candidates;
5. return evidence plus traceable identifiers;
6. expose enough decision metadata for auditing without returning unauthorized content.

## 10. Mock SharePoint Contract

The lab uses a local service to simulate permission behavior without enterprise credentials.

### Content endpoint

```http
GET /items
```

Example:

```json
[
  {
    "id": "doc-hr-001",
    "name": "Q3 Compensation Review.md",
    "site": "HR",
    "path": "/sites/HR/Shared Documents/Compensation",
    "content": "...",
    "sensitivityLabel": "Confidential"
  }
]
```

### Permission endpoint

```http
GET /items/{id}/permissions
```

Example:

```json
{
  "id": "doc-hr-001",
  "uniquePermissions": true,
  "permissions": [
    {"principal": "user:alice@company.com", "roles": ["read"]},
    {"principal": "group:hr-managers", "roles": ["read"]}
  ],
  "inheritedFrom": null,
  "sensitivityLabel": "Confidential"
}
```

The retriever may use live ACL checks or an ingestion-time permission snapshot. The lab should demonstrate the trade-off between fidelity and staleness rather than treating those options as equivalent.

## 11. PostgreSQL and pgvector Data Model

Conceptual tables:

```sql
CREATE TABLE document_chunks (
    id               BIGSERIAL PRIMARY KEY,
    source           TEXT NOT NULL,
    document_id      TEXT NOT NULL,
    content          TEXT NOT NULL,
    embedding        vector(384),
    allowed_users    TEXT[],
    allowed_groups   TEXT[],
    allowed_roles    TEXT[],
    tenant_id        TEXT,
    site_id          TEXT,
    sensitivity      TEXT,
    metadata         JSONB,
    created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE employee_records (
    id               BIGSERIAL PRIMARY KEY,
    employee_email   TEXT,
    department       TEXT,
    tenant_id        TEXT,
    salary           NUMERIC
);

CREATE TABLE audit_log (
    id                BIGSERIAL PRIMARY KEY,
    request_id        UUID NOT NULL,
    user_id           TEXT NOT NULL,
    principals        TEXT[] NOT NULL,
    query_text        TEXT,
    eligible_chunks   JSONB,
    retrieved_chunks  JSONB,
    context_sent      TEXT,
    model_response    TEXT,
    tools_invoked     JSONB,
    created_at        TIMESTAMPTZ DEFAULT now()
);
```

The final executable schema may evolve during implementation. The security invariants must not.

## 12. Vector Retrieval Rule

Every protected vector query must combine authorization filtering and similarity ranking in one controlled query path.

Conceptually:

```sql
SELECT ...
FROM document_chunks
WHERE
    (
        allowed_users  && :principals
        OR allowed_groups && :principals
        OR allowed_roles  && :principals
    )
    AND (:tenant_id IS NULL OR tenant_id = :tenant_id)
ORDER BY embedding <=> :query_embedding
LIMIT :top_k;
```

The exact SQL must be parameterized.

> **Similarity ranking runs over the authorized candidate set, not over the unrestricted corpus.**

## 13. Prompt Assembly

The application layer owns prompt evidence construction.

It may combine results from multiple retrievers only after each retriever has enforced its source authorization rule. Prompt assembly records stable evidence identifiers so the audit trail can show exactly which authorized chunks entered the context.

The model must never receive raw unrestricted source results.

## 14. Tool Authorization

At least one protected example tool should demonstrate that tool execution is a separate authorization boundary.

```text
model requests tool
  -> application passes IdentityContext
  -> tool validates required authority
  -> permitted result or explicit denial
  -> audit tool decision
```

The tool must not trust the fact that the caller previously passed retrieval authorization.

## 15. Audit Model

For each request, record enough evidence to reconstruct the model-input path.

Minimum fields:

- request ID;
- user ID;
- canonical principals;
- query text;
- source adapters consulted;
- eligible evidence identifiers;
- retrieved evidence identifiers;
- exact context sent to the model;
- model response;
- tools invoked and authorization outcome;
- timestamp.

Sensitive production logging concerns are outside the first lab, but audit capture must not become a reason to duplicate unrestricted source data.

## 16. Threat Model

| Threat | Design response |
|---|---|
| Post-filter leakage | authorization-first pre-filter on every protected source |
| Confused deputy | no unrestricted privileged read followed by user-side trimming |
| Inconsistent identity mapping | one validated immutable `IdentityContext` with canonical principals |
| Stale document ACL snapshot | ability to compare stored metadata with live-style permission checks |
| Vector-store ACL bypass | mandatory authorization predicate in vector query path |
| Over-privileged tool | tool re-validates caller authority independently |
| Prompt evidence leakage | prompt assembled only from already-authorized retriever outputs |
| Missing forensic evidence | request audit captures the complete authorized evidence path |

## 17. Verification Requirements

Implementation is not complete until the following behaviors have executable evidence.

### Authentication tests

- valid token produces expected `IdentityContext`;
- missing token fails;
- invalid token fails;
- expected roles/groups/principals resolve deterministically.

### Retrieval tests

- authorized user receives permitted documents;
- different user cannot retrieve the same restricted documents;
- structured database rows obey row/principal rules;
- vector retrieval cannot return chunks outside the caller's principals.

### Context-boundary tests

- unauthorized chunks never appear in assembled context;
- cross-user tests inspect `context_sent`, not only final answer text.

### Tool tests

- authorized caller succeeds;
- unauthorized caller is denied;
- denial is recorded.

### Audit tests

- audit data identifies eligible and retrieved evidence;
- exact model context is reconstructible;
- tool authorization outcome is visible.

## 18. Repository Layout for Future Implementation

The pattern folder remains documentation-only while maturity is **DESIGNED**.

When implementation begins, use the repository's Clean Architecture rules and keep provider/framework dependencies out of Domain.

```text
patterns/12_identity_aware_retrieval/
├── README.md
├── TECH_SPEC.md
├── src/
│   ├── domain/
│   │   ├── identity.py
│   │   ├── evidence.py
│   │   └── ports/
│   │       ├── retriever.py
│   │       └── audit.py
│   ├── application/
│   │   ├── query_use_case.py
│   │   └── prompt_assembly.py
│   ├── infrastructure/
│   │   ├── auth0/
│   │   ├── mock_sharepoint/
│   │   ├── postgres/
│   │   └── pgvector/
│   └── api/
│       └── fastapi/
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   │   └── infrastructure/
│   └── acceptance/
└── docs/
    └── adrs/
```

This is a target layout, not a claim that the files already exist.

Any implementation-time architectural decision that changes a meaningful boundary must be captured in an ADR according to repository conventions.

## 19. Technology Choices

| Layer | Initial choice |
|---|---|
| Identity provider | Auth0 free tier |
| API framework | FastAPI |
| Database | PostgreSQL 16 |
| Vector extension | pgvector |
| Mock document source | FastAPI Mock SharePoint service |
| Local orchestration | Python 3.11+ |
| Containers | Docker Compose |
| JWT validation | maintained Auth0-compatible Python library selected during implementation |

Third-party dependencies must be introduced only when the implementation slice requires them.

## 20. Future Extensions

Possible later exercises:

- continuous ACL synchronization and permission-drift detection;
- real Entra ID / Microsoft Graph integration;
- relationship-based authorization with OpenFGA or SpiceDB;
- stronger tenant isolation;
- source-level delegated authorization;
- streaming with safe audit semantics;
- cache authorization and identity-aware invalidation;
- authorization-aware reranking;
- tool/action policy decisions beyond read-only examples.

These remain outside Pattern 12 v1.0 until explicitly promoted into scope.

## 21. Maturity and Evidence Rule

This document defines the target architecture and verification contract.

The pattern is **DESIGNED**, not **BUILDING** or **VERIFIED**.

Promotion requires:

- **BUILDING** — executable implementation work has started and repository evidence exists;
- **VERIFIED** — the intended authorization paths and negative failure paths have been executed successfully, with inspectable test and audit evidence.

No maturity claim should exceed the evidence present in the repository.
