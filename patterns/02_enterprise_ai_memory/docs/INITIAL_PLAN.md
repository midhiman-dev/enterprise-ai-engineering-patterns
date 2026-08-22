# Pattern 02 — Designing Reliable AI Memory for Enterprise Systems

## Use Case

**Enterprise HR Service Desk Assistant**

A workforce-scale AI assistant serving thousands of employees with questions related to leave and PTO, payroll, employee benefits, HR policies, previously raised HR issues, and standard HR procedures.

The purpose of this pattern is not to build another HR chatbot. It exists to teach how enterprise AI systems should manage memory reliably across many users, multiple sessions, changing policies, authoritative enterprise systems, and partial infrastructure failures.

The central engineering question is:

> What should an enterprise AI system remember, for whom, for how long, from which source, with what consistency guarantees, and what should happen when memory infrastructure becomes slow, stale, unavailable, or unsafe?

---

## 1. Core Learning Objective

Pattern 02 teaches how to design a memory architecture that supports:

- short-lived conversational state
- cross-session historical context
- organizational knowledge
- procedural rules
- authoritative enterprise data access
- horizontal scaling
- graceful degradation
- versioned knowledge
- privacy isolation
- retention and forgetting
- observability
- measurable reliability

The primary learning theme is:

> Reliable enterprise AI memory is not just storage. It is controlled context management across different kinds of state with different authority, lifecycle, consistency, privacy, and availability requirements.

---

## 2. Why This Is a Separate Pattern

Pattern 01 — Corrective RAG — focuses primarily on:

> Can the system retrieve sufficiently trustworthy information to answer a question?

Pattern 02 focuses on a different problem:

> What should the system remember, what must it re-fetch, whose memory is it, how fresh is it, and what happens when one part of memory fails?

Pattern 02 therefore introduces capabilities not substantially covered by Pattern 01:

- working memory
- episodic memory
- semantic memory lifecycle
- procedural memory
- cross-session context
- authoritative-data boundaries
- memory isolation
- context construction
- memory consistency
- graceful degradation
- version switching
- memory retention
- forgetting
- high-concurrency state access
- load testing
- reliability measurements

---

## 3. Primary Persona

**Employee using an internal HR self-service assistant.**

Secondary stakeholders include HR operations, payroll operations, benefits administrators, enterprise platform teams, and security/compliance teams, but the tutorial remains centered on the employee journey.

---

## 4. Critical Architectural Principle — Memory Is Not Enterprise Truth

The system explicitly distinguishes between AI memory and authoritative enterprise state.

### AI memory

Context that helps the AI understand or continue an interaction.

Examples:

- current conversation
- previously discussed HR issues
- known user preferences
- historical interactions
- policy knowledge
- workflow rules

### Authoritative enterprise state

Facts owned by enterprise systems of record.

Examples:

- current PTO balance
- salary amount
- payroll status
- benefit enrollment
- employee master data
- case status

The assistant must never treat remembered values as authoritative simply because they were previously observed.

Example:

```text
Employee:
"How much PTO do I have?"

Wrong design:

episodic memory
→ "Last week you had 17.5 days"
→ answer 17.5

Correct design:

conversation context
→ identify leave-balance intent
→ authoritative leave service
→ current balance = 16.5
→ explain current value
```

Architectural rule:

> Memory provides context. Systems of record provide authoritative facts.

---

## 5. Memory Model

The system uses four explicitly defined memory types.

### 5.1 Working Memory

Purpose: short-lived conversational state required to continue the current interaction.

Examples:

- current conversation messages
- current topic
- resolved references such as "that payroll issue"
- short-lived intermediate context
- current workflow state

Characteristics:

- high read/write frequency
- low-latency requirement
- short TTL
- disposable
- not authoritative
- employee/session scoped

Initial infrastructure: **Redis-compatible distributed cache**.

Application code depends on a `WorkingMemory` port rather than Redis APIs directly.

### 5.2 Episodic Memory

Purpose: historical events and interactions associated with an employee.

Examples:

- previous HR conversations
- prior payroll dispute discussion
- previously raised case reference
- resolution summaries
- significant interaction events

Example:

```text
Monday:
Employee: "My February salary is missing the internet allowance."
Assistant:
→ investigates
→ records interaction episode
→ case HR-4821 becomes associated with the episode

Friday:
Employee: "What happened with my allowance issue?"
Assistant:
→ retrieves relevant previous episode
→ discovers HR-4821
→ verifies current case status from authoritative system
→ answers
```

Important rule:

> Episodic memory may identify the relevant historical event, but current enterprise state must still be verified from the appropriate system of record.

Initial infrastructure: **PostgreSQL**.

### 5.3 Semantic Memory

Purpose: organizational knowledge used to answer policy and informational questions.

Examples:

- parental-leave policy
- payroll calendars
- employee benefits handbook
- leave policies
- HR FAQs
- internal HR guidance

Initial infrastructure: **PostgreSQL + pgvector**.

This is a frozen Pattern 02 decision.

The pattern deliberately uses PostgreSQL + pgvector rather than a separate vector database so it can teach a real architecture trade-off:

> When is consolidating relational and vector workloads into PostgreSQL operationally preferable to deploying a separate vector-store product?

Application code depends on a `SemanticMemory` port rather than pgvector directly.

### 5.4 Procedural Memory

Purpose: rules controlling how the assistant performs approved HR workflows.

Examples:

```text
Payroll discrepancy
→ verify identity
→ fetch payroll record
→ determine payroll-cycle state
→ collect required information
→ escalate if applicable
```

Rules can also express constraints such as:

```text
Payroll discrepancy > ₹25,000
→ human approval required before escalation
```

Characteristics:

- read frequently
- changes comparatively rarely
- versioned
- auditable
- effective-date aware
- locally cacheable
- not embedded inside LLM prompts as untraceable static text

Initial direction:

```text
versioned procedure definitions
        ↓
active procedure version
        ↓
local application cache
        ↓
version/invalidation check
```

---

## 6. Authoritative Enterprise State

A separate architectural boundary exists outside the AI memory system.

Conceptually:

```text
Authoritative Enterprise Systems

├── Leave Management
├── Payroll
├── Benefits
├── Employee Master
└── HR Case Management
```

For the tutorial these are represented by realistic synthetic systems/data.

Application-facing ports may include:

```text
EmployeeDataProvider
LeaveBalanceProvider
PayrollProvider
BenefitsProvider
HrCaseProvider
```

The tutorial does not require proprietary Workday, SAP SuccessFactors, Oracle HCM, or similar credentials.

---

## 7. High-Level System Design

```text
                       ┌──────────────────────┐
                       │     Employee UI      │
                       │  HR Self-Service Chat│
                       └──────────┬───────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │ API Gateway /        │
                       │ Load Balancer        │
                       │ routing              │
                       │ rate limiting        │
                       │ burst protection     │
                       └──────────┬───────────┘
                                  │
                                  ▼
              ┌─────────────────────────────────────┐
              │        Stateless API Layer          │
              │        horizontally scalable        │
              └──────────────────┬──────────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │      Assistant Application          │
              │ intent / workflow orchestration     │
              │ context construction                │
              │ authorization                       │
              │ degradation decisions               │
              └──────────────────┬──────────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │        Memory Orchestrator          │
              │ scoped access                       │
              │ timeout policy                      │
              │ circuit breakers                    │
              │ fallback decisions                  │
              │ version tracking                    │
              └───────┬────────┬────────┬───────────┘
                      │        │        │
          ┌───────────┘        │        └───────────┐
          ▼                    ▼                    ▼

 ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐
 │ Working Memory │   │Episodic Memory │   │ Semantic Memory    │
 │ Redis          │   │ PostgreSQL     │   │ PostgreSQL         │
 │ TTL/session    │   │ employee       │   │ + pgvector         │
 │ scoped         │   │ history        │   │ versioned policies │
 └────────────────┘   └────────────────┘   └────────────────────┘

                               │
                               ▼
                     ┌──────────────────┐
                     │ Procedural Memory│
                     │ versioned rules  │
                     │ local cache      │
                     │ effective dates  │
                     └──────────────────┘

              ───────── AUTHORITATIVE BOUNDARY ─────────

                                 │
                                 ▼

               ┌───────────────────────────────────┐
               │ Enterprise Data / Tool Ports      │
               └──────┬────────┬────────┬─────────┘
                      │        │        │
                      ▼        ▼        ▼
                    Leave    Payroll  Benefits
                      │        │        │
                      └────────┼────────┘
                               ▼
                      Synthetic Systems
                         of Record
```

---

## 8. Stateless Application Design

API instances must be stateless. No request may require affinity with a specific API instance.

```text
Request 1 → API instance A
Request 2 → API instance D
Request 3 → API instance B
```

Session state belongs in Working Memory rather than process memory. Local caches may exist only for immutable/versioned or safely reloadable data such as procedural rules.

---

## 9. Memory Orchestrator

Responsibilities include:

- employee/session scoping
- retrieval orchestration
- memory timeouts
- circuit-breaker state
- memory-source availability
- version tracking
- context assembly
- degradation decisions
- tracing

It must not simply query every memory store. Memory access depends on the use case.

Example:

```text
"How much leave do I have?"
Needs:
working memory
authoritative leave service

May not need:
semantic memory
episodic memory
```

---

## 10. Graceful Degradation Principle

Failure of one memory system must not automatically fail the entire assistant.

However:

> Graceful degradation does not mean generating an answer from whatever information happens to remain available.

Example:

```text
Question: "How many PTO days do I have?"
Semantic memory unavailable
→ irrelevant to current request
→ authoritative leave service available
→ request succeeds
```

But:

```text
Question: "What is our current parental-leave policy?"
Semantic memory unavailable
→ authoritative policy knowledge unavailable
→ do not invent from working/episodic memory
→ capability-level safe failure
```

---

## 11. Versioned Semantic Memory

HR policy updates must not be uncontrolled in-place vector changes.

Example:

```text
parental-leave-v17
parental-leave-v18
```

Lifecycle:

```text
new policy received
        ↓
validate source
        ↓
chunk
        ↓
embed
        ↓
build candidate version
        ↓
run evaluation
        ↓
mark READY
        ↓
atomically change active version
```

If evaluation fails, the prior version remains active.

Each generated answer should be traceable to a semantic-memory version where applicable.

---

## 12. Procedural Memory Versioning

Procedures are version-aware.

Example:

```text
payroll-dispute-v6
payroll-dispute-v7
```

Execution traces should record the active rule/policy versions where relevant.

---

## 13. Employee Isolation

Employee memory must be isolated before it reaches LLM context.

Unacceptable:

```text
retrieve broadly
→ send everything to LLM
→ prompt the LLM not to disclose it
```

Required:

```text
authenticated identity
        ↓
authorization scope
        ↓
employee-filtered retrieval
        ↓
approved context
        ↓
LLM
```

Cross-employee episodic-memory leakage is a critical failure.

---

## 14. Memory Lifecycle and Forgetting

### Working Memory

Short-lived, with TTL measured in minutes or hours.

### Episodic Memory

Longer lived but governed by configurable retention, deletion, redaction, expiry, and audit metadata.

### Semantic Memory

```text
draft
→ candidate
→ active
→ superseded
→ archived
```

### Procedural Memory

```text
draft
→ approved
→ active
→ superseded
```

---

## 15. Golden Scenarios

### Scenario 1 — New-Year Leave-Balance Burst

At the beginning of the year, 8,000 employees ask variations of:

> "How much leave do I have available?"

Expected flow:

```text
request
→ gateway/load balancer
→ stateless API instance
→ authenticated employee scope
→ working-memory lookup
→ authoritative leave-balance provider
→ response
→ memory/event update
```

Measure requests/sec, p50/p95/p99 latency, error rate, working-memory latency, and database/tool latency.

### Scenario 2 — Semantic Memory Failure Mid-Request

The pgvector-backed semantic-memory capability becomes unavailable or exceeds its latency budget.

For a current-policy query, the system must use a circuit breaker and return a controlled degraded response rather than substitute stale or unrelated context.

### Scenario 3 — Atomic Policy Rollout

HR publishes a new parental-leave policy.

```text
parental-leave-v17
→ parental-leave-v18 candidate
→ ingest
→ embed
→ evaluate
→ mark READY
→ atomic activation
```

If evaluation fails, v17 remains active.

### Scenario 4 — Cross-Session Episodic Recall

A later session retrieves the prior payroll interaction, identifies case `HR-4821`, then verifies current case status from the authoritative provider before answering.

### Scenario 5 — Cross-Employee Memory Leakage Attempt

An employee attempts to retrieve another employee's payroll issue or equivalent sensitive context. Authorization must prevent prohibited memory from entering prompt context.

Success condition:

```text
zero unauthorized episodic records retrieved
```

---

## 16. Evaluation Strategy

The pattern should produce measurable evidence across:

- reliability: success rate, p50/p95/p99, dependency timeouts, circuit-breaker transitions
- isolation: zero cross-employee episodic retrievals
- policy consistency: all new requests use the active semantic version after cutover
- episodic recall: relevant-event hit rate and false episode retrieval rate
- freshness: inactive semantic/procedural versions are not used for new requests
- retention: working-memory expiry and episodic deletion/redaction
- authority boundary: PTO, payroll, benefits, and case status never come solely from remembered values

---

## 17. Technology Direction

Frozen baseline:

```text
Language: Python
API: FastAPI
Working memory: Redis-compatible store
Episodic memory: PostgreSQL
Semantic memory: PostgreSQL + pgvector
Procedural memory: versioned rules/configuration with local read cache
LLM: provider-neutral abstraction; Groq initially where practical
Load testing: Locust or k6 — final choice deferred
Telemetry: OpenTelemetry
Containers: Docker / Docker Compose
UI: React + TypeScript
```

---

## 18. Why PostgreSQL + pgvector

Pattern 02 uses PostgreSQL + pgvector deliberately because:

1. PostgreSQL already supports episodic relational data.
2. pgvector adds semantic similarity search without introducing another infrastructure product.
3. The pattern can teach the trade-off between infrastructure consolidation and specialized vector databases.
4. Local development remains relatively simple.
5. Domain/Application remain provider-neutral through memory ports.

This does not imply PostgreSQL + pgvector is always the correct enterprise vector architecture.

Production evolution should compare PostgreSQL + pgvector with a dedicated vector search platform based on corpus size, throughput, indexing behavior, hybrid-search needs, operational complexity, availability, filtering patterns, and cost.

---

## 19. Clean Architecture Direction — Aligned with Pattern 01 Repository Conventions

Pattern 01 currently uses the repository convention:

```text
patterns/<pattern_name>/
├── README.md
├── data/
├── docs/
├── pyproject.toml
├── scripts/
├── src/
│   └── <python_package>/
│       ├── __init__.py
│       ├── api/
│       ├── application/
│       ├── composition/
│       ├── domain/
│       └── infrastructure/
└── tests/
```

Pattern 02 should follow the same shape.

Conceptual structure:

```text
patterns/02_enterprise_ai_memory/
├── README.md
├── data/
├── docs/
│   ├── INITIAL_PLAN.md
│   └── adr/
├── pyproject.toml
├── scripts/
├── src/
│   └── enterprise_ai_memory/
│       ├── __init__.py
│       ├── api/
│       ├── application/
│       │   ├── memory/
│       │   ├── context/
│       │   ├── workflows/
│       │   ├── reliability/
│       │   └── authorization/
│       ├── composition/
│       ├── domain/
│       │   ├── entities/
│       │   ├── value_objects/
│       │   └── ports/
│       └── infrastructure/
│           ├── working_memory/
│           ├── episodic_memory/
│           ├── semantic_memory/
│           ├── procedural_memory/
│           ├── enterprise_data/
│           ├── llm/
│           └── telemetry/
└── tests/
```

Important convention:

> `src/enterprise_ai_memory/` is the Python package inside `patterns/02_enterprise_ai_memory/`, matching Pattern 01's `patterns/01_corrective_rag/src/corrective_rag/` convention.

Likely ports include:

```text
WorkingMemory
EpisodicMemory
SemanticMemory
ProceduralMemory
LeaveBalanceProvider
PayrollProvider
BenefitsProvider
HrCaseProvider
Generator
Clock
IdentityContext
```

Provider/product names remain Infrastructure concerns.

---

## 20. Failure Modes to Teach

Where practical, test or simulate:

- Redis unavailable
- Redis latency spike
- PostgreSQL unavailable
- pgvector semantic query timeout
- stale semantic version
- incomplete policy ingestion
- procedural-cache staleness
- cross-user memory leakage
- excessive context growth
- duplicate episodic events
- stale authoritative value reused from memory
- connection-pool exhaustion
- retry storms
- circuit-breaker misconfiguration
- partial dependency outage
- memory deletion failure

---

## 21. Deliberately Not in Scope

The initial pattern will not build:

- complete HRMS
- payroll engine
- benefits platform
- real Workday integration
- real SAP SuccessFactors integration
- enterprise SSO implementation
- multi-region database replication
- Kubernetes production deployment
- multi-agent architecture
- full legal/compliance framework
- complete HR case-management application
- millions-of-users benchmark
- production-grade disaster-recovery environment

These may be discussed as design-only production evolution.

---

## 22. Scaling Philosophy

The tutorial will not introduce infrastructure complexity solely to appear enterprise-scale.

Initial implementation may use:

```text
PostgreSQL
+ appropriate indexes
+ connection pooling
```

and Redis behind a provider-neutral port.

Load/failure testing should determine what scalability changes become justified.

Production evolution may discuss Redis Cluster, read replicas, partitioning, multi-AZ deployment, failover, connection proxies, and dedicated vector infrastructure.

All claims must be labeled as:

```text
Implemented
Tested
Measured
Design-only
```

---

## 23. Key ADRs

The implementation should eventually capture at least:

1. Why four memory categories are modeled separately
2. Why enterprise transactional state is not AI memory
3. Why PostgreSQL + pgvector was selected for semantic memory
4. Why API instances remain stateless
5. Why semantic memory uses versioned knowledge sets
6. Why capability-specific graceful degradation is used
7. Why authorization occurs before context construction
8. Why procedural memory is versioned
9. Why retry behavior is bounded
10. Why infrastructure scaling features are introduced only when evidence justifies them

---

## 24. Interview Questions Covered

This pattern should provide concrete evidence for discussing:

- working vs episodic vs semantic memory
- persistence across sessions
- what AI systems should not remember
- freshness and forgetting
- failure of memory subsystems
- graceful degradation
- circuit breakers and latency budgets
- horizontal scaling of stateful user experiences
- Redis clustering and PostgreSQL partitioning trade-offs
- cross-user memory isolation
- prompt-level authorization limitations
- safe vector knowledge updates and rollback
- PostgreSQL + pgvector vs dedicated vector databases
- AI memory vs enterprise systems of record

---

## 25. Portfolio Story

```text
Pattern 01 — Corrective RAG

Can the AI obtain enough trustworthy
knowledge to answer correctly?

                  ↓

Pattern 02 — Reliable Enterprise AI Memory

What should the AI remember?
What must remain authoritative elsewhere?
Whose context may it access?
How fresh is memory?
What happens when memory infrastructure fails?
```

---

## 26. Frozen Pattern Definition

**Pattern:** Pattern 02 — Designing Reliable AI Memory for Enterprise Systems

**Use Case:** Enterprise HR Service Desk Assistant

**Core Thesis:**

> Design a horizontally scalable enterprise AI assistant that uses working, episodic, semantic, and procedural memory while preserving authoritative-system boundaries, employee isolation, controlled memory lifecycle, consistent policy updates, graceful degradation, and measurable reliability.

**Semantic Storage Decision:**

> PostgreSQL + pgvector is the selected semantic-memory technology for Pattern 02.

**Golden Scenarios:**

1. New-year leave-balance traffic burst
2. Semantic-memory outage and graceful degradation
3. Atomic parental-leave policy rollout
4. Cross-session episodic recall with authoritative status verification
5. Cross-employee memory leakage prevention

**Status:** FROZEN — Approved as Pattern 02 build candidate.

Detailed implementation passes, exact schemas, Redis deployment topology, load-test tool selection, procedural-rule representation, and lower-level decisions remain intentionally deferred to the dedicated Pattern 02 build thread.
