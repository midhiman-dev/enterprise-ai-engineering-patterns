# Pattern 11 — A2A Agent Interoperability: Cross-Boundary Agent Collaboration

**Current maturity:** **DESIGNED**

## Purpose

This pattern studies **when and why an enterprise architecture should introduce the Agent2Agent (A2A) Protocol** for collaboration between independent agent systems.

The goal is not to build a multi-agent demo for its own sake. The goal is to make an architectural decision that can be defended:

> **When should one agent collaborate with another independent agent over A2A, and when should the interaction remain a direct API call, an MCP tool call, a framework-native sub-agent, or an event/message contract?**

The reference exercise is a bounded **manufacturing component-shortage resolution** workflow.

The pattern is intentionally **C#/.NET-first** because the official A2A project provides a .NET SDK and .NET samples. Other languages/frameworks are introduced only when they add a specific interoperability lesson.

---

## Core Mental Model

> **MCP gives an agent tools. A2A gives an agent peers.**

A practical architecture view:

```text
                    A2A
        ┌────────────────────────────┐
        │ independent agent systems  │
        │ ownership / trust boundary │
        └────────────────────────────┘
             ▲                  ▲
             │                  │
             │                  │
      Planning / Host      Procurement Agent
             │                  │
             │ MCP / API        │ MCP / API
             ▼                  ▼
        Planning tools      ERP / Supplier tools
```

A2A is the horizontal collaboration boundary.

MCP, direct APIs, and ordinary tool calling remain inside an agent's capability boundary.

---

## Central Architecture Decision

Before implementing A2A, answer these questions.

### Strong signals for A2A

Use A2A when several of these are true:

- the remote capability is itself an **independent agentic system**, not merely a deterministic tool;
- agents are owned by different teams, departments, vendors, or organizations;
- agents are independently deployed and versioned;
- agents may use different frameworks or languages;
- the caller should not need the remote agent's prompts, memory, tools, or internal reasoning implementation;
- capability discovery through an Agent Card is useful;
- work may be long-running, streamed, resumed, or require additional input;
- structured artifacts must be exchanged across an agent boundary;
- the interaction crosses a meaningful identity, trust, or governance boundary;
- point-to-point custom agent integrations would otherwise multiply.

### Prefer MCP or normal tool calling when

- one agent needs a database, API, file system, search provider, calculator, or deterministic business capability;
- the capability is naturally expressed as a typed tool operation;
- there is no independent remote agent lifecycle;
- discovery, task lifecycle, and peer collaboration add no value.

### Prefer framework-native multi-agent primitives when

- all agents are part of one application;
- one team owns the whole runtime;
- agents share the same deployment, memory model, orchestration framework, and trust boundary;
- the separation is mainly an implementation technique rather than an enterprise boundary.

### Prefer a direct API when

- the remote system exposes a stable deterministic service contract;
- request/response semantics are enough;
- the caller does not need agent discovery, task lifecycle, conversational continuation, or agent-level artifacts.

### Prefer events/messages when

- the interaction is primarily a business event or command between systems;
- decoupled delivery, replay, fan-out, ordering, or transactional messaging is the main requirement;
- no peer-agent negotiation or conversational task model is required.

### Architect's rule

> **Do not introduce A2A because there are two classes called Agent. Introduce A2A when there are two independently governed agent systems that benefit from a standard collaboration contract.**

---

## Why This Is a Separate Pattern

Pattern 03 asks:

> **What external capability may the AI invoke, through which tool/integration boundary, and under what control?**

Pattern 11 asks:

> **When should an independent agent collaborate with another independent agent, and how should that collaboration be discovered, secured, observed, tested, and governed?**

The distinction is:

```text
Pattern 03 — Agent → Tool / Capability
Pattern 11 — Agent ↔ Agent
```

Pattern 09 complements this pattern:

- Pattern 09 controls context, loops, permissions, recovery, and runtime governance inside an agentic system.
- Pattern 11 defines the interoperability boundary between independent agentic systems.

Pattern 10 remains authoritative for domain invariants:

- an A2A message may propose or request business action;
- the receiving domain still validates and authorizes state changes.

---

# Reference Exercise — Component Shortage Resolution

## Primary persona

**Production planner / supply-chain planner**

The planner receives an alert that confirmed inventory and inbound supply will not cover an upcoming production requirement.

The learning workflow should remain narrow:

> Given one component shortage, coordinate independent specialist agents to produce a traceable resolution recommendation.

This is a learning vehicle for interoperability, not a full procurement platform.

---

## Initial Agent Topology

### 1. Planning / Host Agent

Responsibilities:

- accept the shortage case;
- discover eligible specialist agents;
- validate the selected Agent Card against local policy;
- delegate work;
- track task lifecycle;
- correlate status and artifacts;
- compose a final resolution summary;
- preserve the cross-agent audit trail.

### 2. Procurement Agent

Independently deployed specialist.

Responsibilities:

- evaluate approved suppliers;
- compare lead times and contractual constraints;
- inspect alternate material options;
- return a structured procurement recommendation.

Its internal tools are **not** exposed to the Host. The Procurement Agent may use its own APIs or MCP servers.

### 3. Finance / Risk Agent

Added only after the two-agent path works.

Responsibilities:

- evaluate cost delta;
- assess working-capital impact;
- identify approval threshold;
- return a structured financial/risk artifact.

### 4. Supplier Agent — optional advanced exercise

Represents a different organizational/trust boundary.

Responsibilities may include:

- availability;
- earliest ship date;
- quantity commitment;
- quote validity.

This agent is deliberately deferred because an external trust boundary adds security complexity that should not obscure the first learning objective.

---

## Example Business Input

```json
{
  "shortageCaseId": "SC-1007",
  "sku": "BEARING-X17",
  "requiredQuantity": 1200,
  "availableQuantity": 700,
  "requiredBy": "2026-10-15",
  "productionOrder": "PO-48291",
  "riskLevel": "HIGH"
}
```

The exact payload may evolve. It should remain a **business contract**, not a dump of one agent's private memory or prompt state.

---

## Target Collaboration Flow

```text
Planner / User
      │
      ▼
Planning / Host Agent
      │
      │ discover + validate Agent Card
      ▼
Procurement Agent
      │
      │ uses internal MCP/API tools
      │
      ├── status updates
      ├── input-required if needed
      └── structured recommendation artifact
      │
      │ optional later delegation
      ▼
Finance / Risk Agent
      │
      └── cost / approval / risk artifact
      │
      ▼
Planning / Host Agent
      │
      ├── correlate artifacts
      ├── apply deterministic policy checks
      ├── produce final recommendation
      └── persist delegation/audit trace
```

---

# Protocol Concepts to Learn

The implementation should be pinned to a documented **A2A v1.x** protocol/SDK version.

Core concepts to understand from code:

- A2A Client / Client Agent;
- A2A Server / Remote Agent;
- Agent Card;
- Agent Skill;
- supported interfaces / transport binding;
- Message;
- Parts / structured payloads;
- Task;
- TaskStatus;
- Artifact;
- streaming status/artifact updates;
- asynchronous task handling;
- resubscription / recovery where supported;
- authentication/security metadata;
- protocol-version compatibility.

The objective is not memorizing the schema. It is being able to explain what architectural problem each element solves.

---

# Learning Path

Use the repository-wide method:

> **LEARN → RUN → MODIFY → BREAK → OBSERVE → FIX → PROVE → EXPLAIN → OWN**

## Stage 0 — Decision Kata: Is This Really A2A?

Before writing protocol code, classify a set of interactions as:

```text
Direct API
MCP / tool
Framework-native agent
Event / message
A2A
```

Examples:

- fetch inventory balance;
- calculate landed cost;
- ask an independently deployed Procurement Agent to investigate a shortage;
- publish `PurchaseOrderApproved`;
- call an internal sub-agent in the same Semantic Kernel process;
- ask an external Supplier Agent to negotiate availability.

For every answer, write the reason.

**Exit evidence:** an ADR or decision table showing why the component-shortage specialist boundary justifies A2A.

---

## Stage 1 — Protocol Foundations

Study the official A2A v1.x documentation and identify:

- what A2A is;
- what A2A is not;
- A2A vs MCP;
- Agent Card;
- Message;
- Task;
- TaskStatus;
- Artifact;
- standard protocol bindings;
- streaming/asynchronous interaction;
- security model.

**Exit evidence:** one-page architecture notes and a hand-drawn/README mental model.

---

## Stage 2 — Run the Official .NET Samples

Start with the official samples rather than writing a framework abstraction immediately.

Use the .NET sample set to understand:

- basic server;
- basic client;
- Agent Card retrieval;
- message exchange;
- task/status behavior;
- streaming where the sample supports it.

Recommended starting points in the official sample repository:

- `samples/dotnet/BasicA2ADemo`;
- `samples/dotnet/A2ACliDemo`;
- `samples/dotnet/A2ASemanticKernelDemo`.

**Exit evidence:** commands, screenshots/logs, and notes explaining the request lifecycle.

---

## Stage 3 — Build a Minimal .NET Host + Remote Agent

Create two very small applications:

```text
ShortageHost
ProcurementAgent
```

Keep all business logic fake/deterministic at first.

Goals:

- publish a realistic Procurement Agent Card;
- fetch and inspect the card;
- select the required skill;
- send a shortage message;
- return a structured artifact;
- correlate request, task, and result.

No LLM is required yet.

**Reason:** protocol mechanics should be understood before probabilistic behavior is introduced.

---

## Stage 4 — Task Lifecycle and Streaming

Introduce a long-running investigation path.

Exercise states such as:

```text
submitted / accepted
working
input-required
completed
failed
canceled / rejected where applicable
```

Add streamed progress such as:

```text
Supplier shortlist loaded
Lead-time evaluation complete
Alternative material check running
Recommendation ready
```

Deliberately disconnect the stream and exercise the supported recovery/resubscription path.

**Exit evidence:** trace showing state transitions and streamed artifact/status events.

---

## Stage 5 — Add the Finance / Risk Agent

Introduce a second independently deployed specialist.

The Procurement Agent or Host may delegate financial analysis depending on the chosen architecture.

This stage should force an explicit ADR:

> **Who owns orchestration — the Host, or may specialist agents delegate further?**

Test both conceptually before selecting one.

**Exit evidence:** a multi-hop trace with clear task ownership and correlation.

---

## Stage 6 — Introduce Heterogeneity Deliberately

Only now add a second implementation stack, for example:

- Host: C#/.NET;
- Procurement: C#/.NET;
- Finance/Risk: Python, JavaScript, Java, or another official SDK.

The objective is to prove **protocol interoperability**, not compare frameworks.

**Exit evidence:** one working cross-language task with the same business contract.

---

## Stage 7 — Combine A2A + MCP Correctly

Inside one specialist agent, use MCP for tool/resource access.

Example:

```text
Host Agent
   │
   │ A2A
   ▼
Procurement Agent
   │
   ├── MCP → approved supplier catalog
   ├── MCP → contract lookup
   └── API → lead-time service
```

The Host must not become aware of the Procurement Agent's private MCP topology.

**Exit evidence:** architecture diagram showing the horizontal A2A boundary and vertical MCP/tool boundaries.

---

## Stage 8 — Security and Trust Boundary

Treat every remote agent as untrusted unless explicitly trusted by policy.

Exercise:

- Agent Card validation;
- protocol-version checks;
- endpoint allowlisting;
- authentication failure;
- malformed or oversized messages;
- malicious text inside Agent Card fields;
- prompt-injection-like content in remote messages/artifacts;
- least-privilege credentials;
- sensitive-data filtering;
- cross-tenant/cross-user task isolation;
- approval before consequential writes.

Important principle:

> **Opacity protects implementation independence; it does not create trust.**

---

## Stage 9 — Observability and Auditability

Create one cross-agent trace that can answer:

- who initiated the case?
- which agent was discovered?
- which Agent Card/version was used?
- what skill was selected?
- which task IDs and correlation IDs were created?
- which statuses occurred?
- how long did each delegation take?
- which artifacts were returned?
- what validation/policy checks ran?
- what failed or retried?
- where did human approval occur?
- what final outcome was composed?

Recommended telemetry concepts:

- correlation ID;
- local task ID;
- remote task ID;
- agent identity;
- skill ID;
- protocol version;
- transport;
- status transitions;
- latency;
- retry/resubscription count;
- artifact metadata/hash;
- policy decision;
- terminal outcome.

Do not log hidden reasoning or secrets merely to make the trace look complete.

---

## Stage 10 — Break the System

Deliberately exercise:

- stale Agent Card;
- incompatible protocol version;
- wrong/unknown skill;
- remote agent unavailable;
- authentication failure;
- authorization denial;
- malformed artifact;
- task stuck in working state;
- repeated input-required loop;
- SSE/stream disconnect;
- duplicate/replayed request;
- conflicting supplier information;
- downstream agent failure during multi-hop delegation;
- malicious Agent Card content;
- malicious artifact content;
- task completion reported without required artifact.

For every failure define:

```text
Detection
→ Classification
→ Retry / no-retry
→ Escalation
→ Evidence
→ Terminal state
```

---

## Stage 11 — Protocol Validation

Use the official A2A validation/testing tooling where practical:

- A2A Inspector;
- A2A Technology Compatibility Kit (TCK);
- interoperability tooling provided by the A2A project.

The goal is to verify more than “my two apps happen to talk to each other.”

---

# Security Model

The pattern should assume:

> **Remote Agent = network peer + autonomous software + untrusted input source**

Controls should include:

- TLS for network transport;
- explicit authentication and authorization;
- trusted/allowed agent registry for enterprise scenarios;
- Agent Card schema/version validation;
- endpoint and redirect restrictions;
- payload size limits;
- timeout and cancellation policy;
- input sanitization before remote content is placed into LLM context;
- output/artifact schema validation;
- task-scoped credentials where possible;
- no transfer of hidden prompts, private memory, or unrelated context;
- human approval before irreversible/high-risk business action;
- auditable delegation chain.

---

# Observability Model

A2A observability is not only HTTP logging.

The trace should connect:

```text
User request
  → Host decision
  → Agent discovery
  → Agent selection
  → Delegated A2A task
  → status / stream events
  → returned artifacts
  → local policy/domain validation
  → final outcome
```

Cross-agent telemetry must distinguish:

- protocol success from business success;
- network failure from remote task failure;
- task completion from artifact validity;
- remote claim from locally verified fact.

---

# Evaluation Strategy

Evaluate the system at multiple layers.

## 1. Protocol correctness

- valid Agent Card;
- compatible protocol version;
- valid task/message/artifact exchange;
- streaming/resubscription behavior;
- correct terminal states.

## 2. Interoperability

- .NET client with .NET server;
- later, .NET client with another official SDK;
- no private framework dependency across the boundary.

## 3. Business-contract quality

- required fields present;
- artifacts conform to schema;
- dates/currency/quantity constraints validated;
- deterministic policies remain outside remote prose.

## 4. Reliability

- timeout;
- retry bounds;
- duplicate handling;
- disconnect recovery;
- failure propagation;
- cancellation.

## 5. Security

- untrusted card/message/artifact handling;
- authentication/authorization;
- prompt-injection resistance at the boundary;
- tenant/task isolation;
- least privilege.

## 6. Observability

- cross-agent correlation;
- status timeline;
- artifact provenance;
- policy decisions;
- terminal outcome.

---

# Verification Criteria

Pattern 11 should not become **VERIFIED** until executable evidence shows that:

- the architecture can justify A2A instead of merely using it;
- a .NET Host discovers and calls a remote A2A agent;
- Agent Card capability selection is explicit and inspectable;
- task lifecycle/status changes are observable;
- a long-running task can stream progress;
- a structured artifact is validated before use;
- duplicate/replayed work does not silently create duplicate business effects;
- remote-agent failure reaches a controlled terminal outcome;
- authentication/authorization failures are handled safely;
- untrusted Agent Card/message/artifact content is not blindly injected into model context;
- a multi-hop or multi-agent trace can be reconstructed;
- at least one cross-language interaction works through the protocol;
- A2A + MCP are demonstrated together without confusing their responsibilities;
- protocol-compliance/interoperability tooling is exercised where practical.

---

# Proposed Repository Shape

Do not scaffold everything before the earlier stages are understood.

Target shape:

```text
patterns/11_a2a_agent_interoperability/
├── README.md
├── tutorial/
│   ├── 01_when_to_use_a2a.md
│   ├── 02_protocol_mental_model.md
│   └── 03_a2a_vs_mcp_api_events.md
├── demo/
│   ├── ShortageHost/
│   └── ProcurementAgent/
├── enterprise/
│   ├── architecture.md
│   ├── security.md
│   ├── observability.md
│   └── evaluation.md
├── adrs/
│   ├── ADR-001-when-to-use-a2a.md
│   ├── ADR-002-orchestration-ownership.md
│   └── ADR-003-remote-agent-trust-model.md
└── tests/
    ├── interoperability/
    ├── failure/
    └── acceptance/
```

Create these folders only as the corresponding learning evidence is produced.

---

# Relationship to Existing Patterns

## Pattern 03 — Tool Calling & MCP

```text
A2A: agent ↔ agent
MCP: agent → tool/resource
```

Pattern 11 should explicitly reuse Pattern 03's lessons about least privilege, structured outputs, approval gates, and auditability.

## Pattern 05 — AI Observability

Provides the telemetry concepts needed for cross-agent traces.

## Pattern 06 — AI System Evaluation

Provides evaluation discipline for protocol, workflow, and AI-quality tests.

## Pattern 07 — Secure & Trustworthy Enterprise AI

Provides security/governance controls that become more important across remote agent boundaries.

## Pattern 09 — Context, Loop & Harness

A remote delegation is still executed inside a governed harness. A2A does not remove the need for bounded loops, permissions, verification, escalation, or audit.

## Pattern 10 — Domain-Driven AI Architecture

A remote agent may recommend an action, but deterministic domain rules still authorize state changes.

---

# Scope Boundaries

This pattern is **not**:

- a full procurement application;
- a supplier marketplace;
- an SAP/Oracle integration project;
- a microservices tutorial;
- a Kubernetes deployment exercise;
- a comparison of every agent framework;
- an autonomous purchase-order approval system;
- a reason to replace ordinary APIs/events with A2A;
- a reason to distribute agents that are simpler as one application.

Initial scope:

- one shortage case;
- Host + Procurement Agent;
- Agent Card discovery/validation;
- A2A task/message/artifact flow;
- streaming task status;
- deterministic fake enterprise data;
- security boundary;
- observability/audit trail;
- failure injection.

Only after that works:

- Finance/Risk Agent;
- cross-language interoperability;
- MCP inside a specialist;
- external Supplier Agent;
- protocol validation tooling.

---

# Interview Recall

## 30-second answer

> “I use A2A when I have independently governed agent systems that need to collaborate across deployment, framework, or organizational boundaries. I would not use A2A for normal tool access — that is where MCP or direct APIs fit — and I would not use it just because an application has multiple internal agents. In the pattern I use a component-shortage workflow: a .NET Host discovers a Procurement Agent through its Agent Card, delegates a task, receives streamed status and structured artifacts, validates them locally, and preserves a cross-agent audit trace.”

## Decision recall

Ask:

```text
Is the remote thing a tool or an agent?
Who owns it?
Is it independently deployed?
Do I need discovery?
Do I need task lifecycle / streaming / async?
Do I need opacity across the boundary?
Does the boundary cross trust/governance domains?
Would REST/events/native orchestration be simpler?
```

If the last question is yes, use the simpler mechanism.

---

# Official Learning Sources

Pin implementation notes to the version actually used.

Primary sources:

- A2A documentation: https://a2a-protocol.org/latest/
- Core specification/governance: https://github.com/a2aproject/A2A
- Official samples: https://github.com/a2aproject/a2a-samples
- Official .NET SDK: https://github.com/a2aproject/a2a-dotnet
- A2A Inspector: https://github.com/a2aproject/a2a-inspector
- A2A TCK: https://github.com/a2aproject/a2a-tck

Use official repositories/specification as the source of truth for protocol behavior.

---

# Maturity Rationale

Current maturity is **DESIGNED** because:

- the architectural decision boundary is defined;
- the reference enterprise workflow is bounded;
- the learning progression is defined;
- security and observability concerns are identified;
- failure modes and verification criteria are defined;
- the relationship with MCP, ordinary APIs/events, framework-native agents, and existing repository patterns is explicit.

It is not **BUILDING** until executable code/evidence begins, and it cannot become **VERIFIED** until the protocol, failure, interoperability, security, and traceability criteria above have executable evidence.
