# Pattern 10 — Domain-Driven AI Architecture: Deterministic Domain, Intelligent Edge

**Current maturity:** **IDENTIFIED**

## Purpose

This pattern explores how to introduce probabilistic AI into a domain-rich enterprise application without allowing AI to redefine, bypass, or weaken authoritative business rules.

The central design question is:

> **How do we integrate probabilistic AI into a domain-rich enterprise application while preserving ubiquitous language, business invariants, consistency boundaries, domain ownership, and deterministic authority?**

The reference implementation will use the existing **Payment & Refund** learning domain so that Domain-Driven Design is learned through a real business workflow rather than as isolated terminology.

The pattern is intentionally not a generic DDD tutorial. It focuses on the intersection between DDD and enterprise AI engineering.

---

## Core Design Principle

> **Deterministic domain, intelligent edge.**

The intended relationship is:

```text
AI / LLM
   │
   │ interpret / classify / suggest / explain
   ▼
Application Use Case
   │
   ▼
Domain Model / Aggregate
   │
   ├── business rules
   ├── invariants
   ├── authority boundaries
   └── valid state transitions
   │
   ▼
Domain Events / Persisted State
```

AI may propose an action.

The domain remains authoritative over whether that action is valid and whether state is allowed to change.

---

## Learning Goals

The pattern should build hands-on understanding of:

- Ubiquitous Language;
- Value Objects;
- Entities;
- Aggregates and Aggregate Roots;
- Domain Events;
- Bounded Contexts;
- application-layer orchestration;
- domain invariants;
- consistency boundaries;
- context boundaries for AI;
- agent/tool capability boundaries;
- deterministic validation around probabilistic interpretation.

Later extensions may include:

- repositories;
- context mapping;
- CQRS;

only where the implementation gives a concrete reason to introduce them.

Event Sourcing is not part of the initial scope.

---

## Reference Domain — Payment & Refund

The reference implementation will evolve from the non-AI Payment & Refund system-design exercise.

Possible domain concepts to explore include:

```text
Payment
Refund
Money
PaymentId
RefundId
PaymentCaptured
RefundRequested
RefundCompleted
```

The exact model is deliberately not frozen here.

The learning exercise should derive the domain model from business rules, invariants, lifecycle, and language rather than copying a predefined class structure.

Possible invariants to investigate:

- a refund amount must be positive;
- total refunds must not exceed the captured payment amount;
- an uncaptured payment cannot be refunded;
- currency must remain consistent;
- invalid state transitions must be rejected;
- duplicate operations must not create duplicate financial effects.

---

## DDD Concepts Applied to AI Engineering

### 1. Ubiquitous Language

Business terminology should remain aligned across:

```text
Business conversation
        ↓
Domain model
        ↓
API / tool contracts
        ↓
Prompt / context terminology
        ↓
Evaluation scenarios
```

Prefer domain capabilities such as:

```text
approve_claim()
request_refund()
capture_payment()
```

over generic interfaces such as:

```text
update_record(status = 3)
```

The AI boundary should speak the same domain language as the business and code.

---

### 2. Value Objects

Use Value Objects where multiple primitive fields form one business concept.

Examples:

```text
Money(amount, currency)
EmailAddress
DateRange
Sku
```

AI should not be responsible for enforcing invariants that the domain model can enforce deterministically.

For example, a refund tool should receive a valid `Money` value rather than a detached numeric amount that loses currency semantics.

---

### 3. Entities

Entities retain business identity through time.

AI may interpret customer language or infer intent, but authoritative identity should come from enterprise systems.

Principle:

> **AI may resolve intent; authoritative systems resolve identity.**

State-changing operations should use stable identifiers such as:

```text
PaymentId
OrderId
CustomerId
ClaimId
```

rather than relying on descriptive similarity.

---

### 4. Aggregates

Aggregates define consistency boundaries and protect invariants.

External callers — including AI agents or AI-assisted workflows — must use the Aggregate Root rather than mutate internal state directly.

Principle:

> **Agents call domain capabilities. They do not bypass aggregates.**

Example conceptually:

```text
AI proposes:
ProcessRefund(paymentId, amount)

        ↓

Application layer

        ↓

Payment aggregate

        ↓

Checks:
- payment captured?
- refundable balance?
- correct currency?
- valid transition?
- duplicate operation?
```

Only after the deterministic checks succeed may state change.

---

### 5. Domain Events

Domain Events expose meaningful business facts without coupling the domain to downstream reactions.

Examples:

```text
PaymentCaptured
RefundRequested
RefundCompleted
PaymentFailed
```

They provide a useful boundary for:

- asynchronous processing;
- auditability;
- notifications;
- analytics;
- future AI consumers;
- distributed workflows.

The domain records what happened.

Downstream systems decide how to react.

---

### 6. Bounded Contexts

A Bounded Context defines where a model and its language are internally consistent.

For AI engineering, this also becomes a **context boundary**.

Principle:

> **Bounded Context → Domain Context Boundary → AI Context Boundary**

An AI use case should receive only the domain concepts and data required for its task.

It should not automatically receive the entire enterprise model merely because those models share the same database or deployment.

Potential contexts around the reference domain may include:

```text
Orders
Payments
Customer Support
Billing
```

The same word may legitimately mean different things in different contexts.

---

## Intended Build Progression

### Stage 1 — Conventional / anemic model

Start with a simple service-oriented model where:

- entities are mostly data containers;
- business rules live in application/service classes;
- state can be mutated too freely.

Observe the problems.

### Stage 2 — Rich domain model

Move domain rules and invariants into appropriate domain objects.

Exercise:

- entities;
- value objects;
- aggregates;
- domain language.

### Stage 3 — Bounded contexts

Separate models where the same concepts have different meanings or responsibilities.

Do not automatically split bounded contexts into microservices.

### Stage 4 — Domain events

Introduce meaningful events and explore:

- asynchronous reactions;
- eventual consistency;
- idempotency;
- event delivery;
- outbox/inbox where appropriate.

### Stage 5 — AI integration

Only after the deterministic domain is stable, introduce AI at the edge.

Possible example:

```text
Customer message
"I was charged twice and want my money back."
        ↓
AI interpretation
        ↓
Intent / extracted proposal
        ↓
Application service
        ↓
Authoritative domain
        ↓
Allowed / rejected / escalated
```

The AI is never the authority for the financial state transition.

---

## Failure Modes to Exercise

The pattern should deliberately test:

- AI proposes an invalid refund amount;
- wrong currency;
- refund exceeds refundable balance;
- duplicate refund proposal;
- stale entity state;
- invalid state transition;
- AI references the wrong entity;
- AI tool tries to bypass the Aggregate Root;
- cross-context data leaks into the wrong AI workflow;
- domain event delivery is duplicated;
- downstream consumer fails after the domain transaction commits.

---

## Verification Goals

The pattern should not be considered VERIFIED until there is executable evidence that:

- domain invariants cannot be bypassed through public APIs/tool calls;
- invalid state transitions are rejected;
- Value Object invariants are enforced;
- Aggregate boundaries are respected;
- Domain Events are emitted only for valid domain transitions;
- duplicate/retried external calls do not create duplicate business effects;
- AI-generated proposals remain subordinate to deterministic domain rules;
- Bounded Context data exposure is explicit and testable;
- important success and failure paths are traceable.

---

## Interview Recall

### 30-second answer

> “I use DDD in AI architecture to keep the business domain authoritative. AI can interpret intent or propose actions, but state changes still pass through domain entities and aggregates that enforce invariants. Bounded Contexts also become useful AI context boundaries, and Domain Events expose meaningful facts without coupling the domain to AI consumers.”

### 90-second answer

Explain:

1. Ubiquitous Language keeps business, code, tools, and prompts aligned.
2. Value Objects and Aggregates encode deterministic invariants.
3. Bounded Contexts constrain both domain meaning and AI context.
4. AI proposes; the domain validates.
5. Domain Events expose valid business facts to downstream consumers.
6. Verification proves that AI cannot bypass domain rules.

### Recall anchors

> **AI interprets; the domain validates.**

> **AI proposes; aggregates authorize state transitions.**

> **Agents call domain capabilities; they do not bypass aggregates.**

> **Bounded Contexts are also context boundaries for AI.**

> **Domain Events expose business facts without making the domain depend on AI.**

---

## Scope Boundary

This pattern is not intended to teach every DDD concept.

Initial scope:

- Ubiquitous Language;
- Value Objects;
- Entities;
- Aggregates;
- Domain Events;
- Bounded Contexts;
- application/domain boundary;
- AI/domain authority boundary.

Deferred unless justified by the implementation:

- repositories;
- domain services;
- context mapping;
- CQRS;
- Event Sourcing.

The goal is implementation-level understanding, not DDD vocabulary coverage.

---

## Learning Method

Use the repository-wide learning loop:

> **LEARN → DESIGN → BUILD → BREAK → OBSERVE → FIX → PROVE → EXPLAIN → OWN**

Pattern 10 should eventually be explainable from code, tests, failure evidence, and domain decisions rather than from the source material alone.
