# Pattern 04 — Designing an Enterprise LLM Gateway & Intelligent Model Routing

## Use Case

**Enterprise-wide LLM Gateway shared by multiple AI applications**

The gateway sits in front of every AI assistant and AI-enabled service in the enterprise, including the HR Service Desk Assistant from Pattern 02 and the E-commerce Order Support & Refunds Assistant from Pattern 03.

The purpose of this pattern is not to build another chatbot. It is to teach how model access becomes a governed enterprise platform capability once multiple teams and applications depend on LLMs.

The central engineering question is:

> How do you centralize model access so compliance, model eligibility, task-aware routing, provider failover, caching, cost attribution, latency tracking, and provider switching become platform concerns rather than duplicated application code?

---

## 1. Core Learning Objective

Pattern 04 teaches how to design an enterprise LLM gateway that can:

- expose one provider-neutral inference surface to multiple upstream applications
- preserve application independence from individual model providers
- apply hard compliance and residency constraints before model optimization
- route by task requirements and model capabilities rather than vendor preference
- maintain configurable task and risk profiles
- select the least costly/lowest-latency model that still satisfies required capability and policy constraints
- fail over between eligible providers without violating compliance rules
- normalize provider-specific request/response behavior behind a canonical gateway contract
- cache only when request, context, security, and freshness semantics make reuse safe
- measure per-request usage, latency, retries, cache behavior, and estimated cost
- attribute usage and cost to authenticated applications/teams
- expose provider health and routing behavior through an operational dashboard
- version routing policy so historical decisions can be reconstructed

The primary learning theme is:

> Enterprise model routing is a policy-and-capability problem, not a hard-coded model-selection problem.

---

## 2. Why This Is a Separate Pattern

Pattern 01 — Corrective RAG — asks:

> What evidence should the system trust?

Pattern 02 — Enterprise AI Memory — asks:

> What should the system remember, for whom, and with what consistency and privacy guarantees?

Pattern 03 — Tool Calling & MCP — asks:

> What external capability may the system invoke, through which boundary, and under what control?

Pattern 04 asks:

> Which model or provider should execute this inference request, under which hard constraints, capability requirements, cost/latency trade-offs, and availability conditions?

The progression is intentionally:

```text
Pattern 01 — KNOW
Pattern 02 — REMEMBER
Pattern 03 — ACT
Pattern 04 — ROUTE
```

Pattern 04 introduces capabilities not substantially covered by the previous patterns:

- enterprise inference gateway
- OpenAI-compatible façade
- canonical request/response normalization
- task profile registry
- risk profile registry
- model capability registry
- versioned routing policy
- hard-constraint filtering
- capability-aware model eligibility
- provider health and circuit breakers
- failover within the eligible set
- context-aware caching
- centralized usage metering
- cost attribution/showback
- routing observability

---

## 3. Primary Users

Pattern 04 deliberately has no end-user chat UI of its own.

The real consumers are upstream AI applications such as:

- HR Service Desk Assistant
- E-commerce Order Support Assistant
- enterprise knowledge assistants
- document-processing services
- future AI-enabled applications

The human-facing UI in this pattern is an **Admin / Platform Operations Dashboard** used by the AI platform team to inspect:

- routing decisions
- requests by application/team
- cost by application/team/model
- latency percentiles
- cache-hit rate
- provider health
- circuit-breaker state
- failover activity
- routing distribution

The gateway itself is service-to-service infrastructure.

---

## 4. Enterprise Problem Being Solved

Without a shared gateway, independent AI applications often evolve like this:

```text
HR Assistant
 → provider SDK
 → retry logic
 → model config
 → cost logging

Order Assistant
 → different provider SDK
 → different retry logic
 → different model config
 → different telemetry

Knowledge Assistant
 → another provider SDK
 → another retry policy
 → another cost model
```

This creates several problems:

- duplicated provider-specific code
- inconsistent retry/failover behavior
- inconsistent observability
- no reliable cross-team cost view
- model/vendor changes require application rewrites
- policy enforcement is spread across teams
- regional/compliance rules can be applied inconsistently
- provider outages have a large application-level blast radius

Pattern 04 changes the architecture to:

```text
AI Applications
       ↓
Enterprise LLM Gateway
       ↓
routing / policy / resilience / telemetry
       ↓
Provider Adapters
```

Architectural principle:

> Inference becomes a governed enterprise platform capability.

---

## 5. Critical Routing Principle — Hard Constraints First, Optimization Second

Routing must not treat all signals as equal preferences.

Some request properties are hard constraints, for example:

- data residency
- approved provider list
- data classification
- required tool-calling support
- required structured-output support
- minimum context window
- security policy

These constraints determine the **eligible model set**.

Only after eligibility is established should the gateway optimize among the remaining candidates using factors such as:

- task complexity
- expected quality
- latency
- cost
- provider health
- historical performance

Conceptually:

```text
Inference Request
       ↓
Hard Policy Constraints
       ↓
Eligible Model Set
       ↓
Capability / Quality Requirement
       ↓
Cost / Latency / Health Optimization
       ↓
Selected Model
```

Architectural rule:

> Compliance constrains routing. It is never merely a weighted preference.

---

## 6. Who Owns Data Classification vs Model Complexity

Pattern 04 separates two fundamentally different decisions.

### 6.1 Data Classification and Residency

The **upstream application and enterprise policy layer** are the primary owners of business/security context because the application knows facts the gateway should not have to infer from arbitrary prompt text.

Examples from the HR assistant:

```text
business_domain = HR
data_classification = PERSONAL
employee_region = EU
residency_requirement = EU
```

The gateway may optionally perform secondary classification or validation, but it must not depend on an LLM guessing whether a request contains protected information.

Principle:

> The application declares trusted business/security context; the gateway enforces it.

### 6.2 Task Type and Complexity

Task type and complexity are routing concerns.

They may originate from:

- trusted metadata from the upstream application
- deterministic request classification in the gateway
- a lightweight classifier introduced later as an optimization

For the baseline pattern, prefer explicit task metadata and deterministic policy over an opaque LLM-based routing classifier.

Examples:

```text
task_type = RESPONSE_FORMATTING
→ low reasoning requirement

task_type = STRUCTURED_EXTRACTION
→ structured-output capability required

task_type = POLICY_INTERPRETATION
→ advanced reasoning capability required
```

Architectural rule:

> A complexity classifier may influence optimization, but it must never override security, compliance, or residency constraints.

---

## 7. Trusted Request Envelope

Every request should carry a trusted caller identity and routing metadata in addition to the inference payload.

Conceptually:

```text
caller:
  app_id = hr-assistant
  team_id = people-platform
  environment = production

policy_context:
  data_classification = personal
  residency = eu

routing_context:
  task_type = policy_interpretation
  risk_hint = high
  tool_result_available = false
```

Application/team identity must come from authenticated service identity or trusted gateway credentials, not arbitrary user-supplied fields.

This allows the gateway to support:

- policy enforcement
- model eligibility
- cost attribution
- showback/chargeback
- auditability
- routing analysis by application/team

---

## 8. Versioned Routing Policy Registry

The gateway should not hard-code business tasks directly to provider/model names.

Instead, Pattern 04 uses a versioned routing-policy registry with four conceptual areas:

```text
Routing Policy Registry
│
├── Task Profiles
├── Risk Profiles
├── Model Profiles
└── Routing Policies
```

The intent is:

> New business task → configuration change where possible.
>
> New platform capability → code change only when the gateway's capability model itself must expand.

---

## 9. Task Profile Registry

Task profiles describe what kind of inference a business task requires.

Examples:

```text
leave_balance_formatting
structured_extraction
customer_chat
policy_interpretation
document_summary
```

Conceptually:

```yaml
task_profiles:
  leave_balance_formatting:
    default_risk: low
    required_capabilities:
      - basic_chat
    preferred_quality_tier: economy

  structured_extraction:
    default_risk: medium
    required_capabilities:
      - structured_output
    preferred_quality_tier: economy

  policy_interpretation:
    default_risk: high
    required_capabilities:
      - advanced_reasoning
    preferred_quality_tier: frontier
```

The registry should resolve tasks to **requirements**, not directly to providers.

Avoid:

```text
policy_interpretation → Provider X
```

Prefer:

```text
policy_interpretation
→ advanced_reasoning
→ minimum quality tier = frontier
```

The gateway then finds the currently eligible model that satisfies those requirements.

---

## 10. Risk Profile Registry

Risk describes how consequential the inference outcome is and constrains what routing choices are acceptable.

Conceptual profiles:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Risk may influence:

- minimum quality tier
- whether experimental models are allowed
- whether fallback below a threshold is permitted
- logging/evaluation expectations
- whether human review is required by an upstream workflow

Example:

```yaml
risk_profiles:
  low:
    min_quality_tier: economy
    allow_experimental: true

  medium:
    min_quality_tier: standard
    allow_experimental: false

  high:
    min_quality_tier: frontier
    allow_fallback_below_minimum: false
```

The upstream application may provide a risk hint, but it must not be able to downgrade a registered minimum simply to obtain a cheaper model.

Conceptually:

```text
effective_risk = max(application_hint, registered_minimum)
```

The exact representation may differ, but the governance principle is frozen.

---

## 11. Model Profile Registry

The gateway should route by model capabilities and policy metadata, not vendor names.

Conceptual `ModelProfile` fields include:

```text
provider
model_id
quality_tier
hosting_class
context_window
supports_tools
supports_structured_output
supports_streaming
reasoning_capability
allowed_regions
input_cost
output_cost
latency_profile
quality_profile
status
policy_tags
```

This allows a request to express requirements such as:

```text
requires_tools = true
requires_eu = true
requires_reasoning = advanced
context_window >= 32k
```

without saying:

```text
use Provider X
```

---

## 12. Capability Tier vs Hosting Class

Pattern 04 should not model `Frontier`, `Fast & Cheap`, and `Self-hosted` as mutually exclusive categories because they describe different dimensions.

### Capability / Quality Tier

Examples:

```text
ECONOMY
STANDARD
FRONTIER
```

### Hosting Class

Examples:

```text
HOSTED_EXTERNAL
HOSTED_REGIONAL
SELF_HOSTED
```

A self-hosted model can itself be economy, standard, or high-capability.

Architectural rule:

> Model capability and deployment location are separate concerns.

---

## 13. Routing Policy Evaluation

The routing engine combines:

```text
task requirements
+
risk constraints
+
data policy
+
model capabilities
+
provider health
+
cost/latency preferences
```

Conceptually:

```text
REQUEST
   │
   ├── Task Profile
   │      ↓
   │  Required Capabilities
   │  + Minimum Risk
   │
   ├── Data Policy
   │      ↓
   │  Region / Provider / Security Constraints
   │
   └──────────────┬──────────────
                  ↓
             Model Registry
                  ↓
           Eligible Candidates
                  ↓
       Cost / Latency / Health
              Optimization
                  ↓
            Selected Model
```

Frozen principle:

> Business tasks are configuration. Platform capabilities are code. Provider selection is runtime policy.

---

## 14. Concrete Routing Examples

### 14.1 Cheap-Model Route — Leave Balance Formatting

The HR assistant has already called an authoritative leave-balance capability and receives:

```text
leave_balance = 14.5
```

The model only needs to format/explain that result.

Expected routing concept:

```text
task_type = leave_balance_formatting
risk = low
required_capability = basic_chat
→ economy tier
```

No frontier model is required simply because the parent application is sophisticated.

### 14.2 Complex Reasoning Route — HR Policy Interpretation

Example:

> "Summarize the company's approved RSU guidance for an employee based in Germany and explain the relevant considerations."

Expected routing concept:

```text
task_type = policy_interpretation
risk = high
required_capability = advanced_reasoning
→ frontier-quality eligible model
```

Authoritative policy/tax content still comes from approved sources; the model is not the system of record or tax authority.

### 14.3 Data Residency Route

Any HR request carrying EU personal-data constraints must route only to models approved for that residency/policy context.

Even a trivial task may not use a cheaper non-EU model.

```text
residency = EU
       ↓
EU-approved eligible set only
       ↓
optimize within that set
```

### 14.4 Provider Outage

If the selected provider is unavailable, the gateway re-evaluates the remaining eligible set.

It must never violate a hard constraint merely to preserve availability.

### 14.5 Repeated Organizational Policy Request

A repeated policy question may be cacheable if the request, security scope, policy version, and context semantics are equivalent.

Personal or tool-derived responses may be explicitly non-cacheable.

---

## 15. OpenAI-Compatible Gateway Surface

The gateway should expose an OpenAI-compatible inference surface, initially centered on:

```text
/v1/chat/completions
```

The adoption advantage is that upstream applications already using compatible SDKs can often point their configured `base_url` to the enterprise gateway rather than importing new provider-specific code.

Architectural caution:

> Protocol compatibility does not imply semantic equivalence between providers.

Providers may differ in:

- tool calling
- structured output
- streaming behavior
- reasoning controls
- context limits
- token accounting
- finish reasons
- error semantics

The gateway therefore needs explicit request/response normalization.

---

## 16. Canonical Request / Response Normalization

Conceptually:

```text
OpenAI-Compatible Request
          ↓
Canonical InferenceRequest
          ↓
Provider Adapter
          ↓
Provider-Specific Request
```

and:

```text
Provider-Specific Response
          ↓
Provider Adapter
          ↓
Canonical InferenceResponse
          ↓
OpenAI-Compatible Response
```

Provider SDKs and provider-specific error models belong in Infrastructure.

The Domain/Application layers should operate on canonical gateway contracts.

---

## 17. Failover and Circuit Breakers

Failover should not mean "retry against the next tier".

It should mean:

```text
selected model fails
       ↓
classify failure
       ↓
re-evaluate remaining eligible candidates
       ↓
select permitted fallback
```

Hard constraints remain in force during failover.

Circuit breakers should be tracked per provider/model endpoint rather than globally.

Example operational states:

```text
Provider A EU       CLOSED
Provider A US       OPEN
Provider B EU       CLOSED
Self-hosted Qwen    HALF_OPEN
```

The routing engine can use provider health as a runtime signal.

Architectural rule:

> Failover is transparent at the integration boundary, not semantically identical at the model-behavior level.

Applications should not need provider-specific failover code, but different models may still produce observably different behavior.

---

## 18. Failure Classification

Not every failure should trigger the same retry or failover behavior.

### Retryable / transient

Examples:

- timeout
- HTTP 429
- temporary provider 5xx
- connection reset

### Candidate failover

Examples:

- circuit breaker open
- regional outage
- provider capacity unavailable

### Do not blindly retry

Examples:

- invalid request
- unsupported tool schema
- context too large
- policy violation
- authentication/authorization failure

This protects against retry storms, duplicate cost, and repeated invalid calls.

---

## 19. Context-Aware Caching

Caching must be policy-controlled rather than implemented as naive prompt deduplication.

A cache key may need to account for concepts such as:

```text
normalized request
policy/context version
security scope
model/routing class
relevant system-prompt version
```

Some requests must be marked non-cacheable.

Examples:

```text
"What is the current parental leave policy?"
→ potentially cacheable when policy/security context matches

"What is my leave balance?"
→ not globally cacheable because result is employee-specific and authoritative state may change
```

Architectural rule:

> Cache only when request, context, freshness, and security semantics make reuse safe.

---

## 20. Usage Metering and Cost Attribution

Every inference request should record directly observable operational metadata such as:

```text
request_id
app_id
team_id
provider
model
routing_policy_version
input_tokens
output_tokens
latency
retry_count
failover_count
cache_hit
result_status
estimated_cost
pricing_version
```

Pricing should be versioned so historical cost reports remain reproducible when provider pricing changes.

The gateway should support questions such as:

- What did each team spend this month?
- Which workloads use frontier models most often?
- How often did failover occur?
- Which provider has the worst p95 latency?
- What percentage of requests were served from cache?

---

## 21. Quality Measurement Is Not the Same as Telemetry

Cost, tokens, latency, errors, and cache hits are directly observable.

Quality often is not.

Pattern 04 should distinguish:

### Directly Measured

```text
provider
model
tokens
latency
errors
retries
cache hits
estimated cost
```

### Derived / Evaluated

```text
quality score
groundedness
task success
human rating
user feedback
```

If quality metadata is stored per request, it should be optional and record its provenance, for example:

```text
quality_score = optional
quality_source = offline_eval | sampled_judge | human_feedback | business_outcome
```

Architectural rule:

> Do not pretend every production response has an objective quality score simply because the dashboard has a column for one.

---

## 22. High-Level System Design

```text
                   Upstream AI Applications
         HR Assistant / Order Support / Others
                          │
                          ▼
              OpenAI-Compatible Gateway API
                          │
                          ▼
                Request Normalization
                          │
                          ▼
                    Routing Engine
        ┌────────────────────────────────────┐
        │ trusted caller / policy metadata   │
        │ task profile                       │
        │ risk profile                       │
        │ hard constraint filtering          │
        │ capability matching                │
        │ provider health                    │
        │ cost / latency optimization        │
        └──────────────────┬─────────────────┘
                           │
                           ▼
                   Routing Decision
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Provider A   Provider B    Self-hosted
          Adapter      Adapter        Adapter
              │            │             │
              ▼            ▼             ▼
        Hosted Model  Hosted Model   vLLM/Ollama

Cross-cutting:

policy registry
cache
usage metering
cost accounting
provider health
circuit breakers
timeouts / bounded retries
audit trace
OpenTelemetry

Operational surface:

Usage / Routing Store
        ↓
Admin Dashboard
```

---

## 23. Clean Architecture Direction — Aligned with Repository Conventions

Pattern 04 should follow the same pattern-level structure used by Patterns 01–03.

Conceptual structure:

```text
patterns/04_llm_gateway_model_routing/
├── README.md
├── data/
├── docs/
│   ├── INITIAL_PLAN.md
│   ├── adrs/
│   ├── tutorial/
│   ├── interview-guide/
│   └── assignment/
├── scripts/
├── src/
│   └── llm_gateway_model_routing/
│       ├── __init__.py
│       ├── api/
│       ├── application/
│       │   ├── routing/
│       │   ├── policy/
│       │   ├── resilience/
│       │   ├── caching/
│       │   └── metering/
│       ├── composition/
│       ├── domain/
│       │   ├── entities/
│       │   ├── value_objects/
│       │   └── ports/
│       └── infrastructure/
│           ├── providers/
│           ├── cache/
│           ├── usage_store/
│           ├── policy_store/
│           ├── identity/
│           └── telemetry/
└── tests/
```

Important convention:

> `src/llm_gateway_model_routing/` is the Python package inside `patterns/04_llm_gateway_model_routing/`, matching the package conventions used by earlier patterns.

Possible Domain/Application abstractions include:

```text
InferenceRequest
InferenceResponse
RoutingDecision
TaskProfile
RiskProfile
ModelProfile
RoutingPolicyVersion
ProviderHealth
UsageRecord

ModelProvider
RoutingPolicyRepository
ModelRegistry
Cache
UsageStore
CostCalculator
Clock
IdentityContext
```

Provider SDKs and product-specific details belong in Infrastructure.

---

## 24. Initial Technology Direction

Initial direction:

```text
Language: Python
Gateway API: FastAPI
Gateway contract: OpenAI-compatible /v1/chat/completions
Admin UI: React + TypeScript
Cache: Redis
Usage/routing store: PostgreSQL
Telemetry: OpenTelemetry
Provider adapters: OpenAI-compatible + Anthropic + Gemini-class adapters
Self-hosted adapter: vLLM or Ollama — final choice deferred
Containers: Docker / Docker Compose
Load testing: k6 or Locust — final choice deferred
```

PostgreSQL is preferred initially over ClickHouse for the tutorial to avoid unnecessary analytical infrastructure before volume justifies it.

A production-evolution section may discuss migration to a dedicated analytical store if telemetry volume requires it.

---

## 25. Admin Dashboard Scope

The Admin Dashboard is initially read-only.

It should visualize operational evidence such as:

- requests by application/team
- cost by team/model/provider
- p50/p95/p99 latency
- routing distribution by task/quality tier
- cache-hit rate
- failover count
- provider health
- circuit-breaker state

Dynamic policy editing through the dashboard is deliberately deferred because it creates a larger governance and approval surface.

Baseline policy can be stored as versioned configuration.

---

## 26. Candidate Golden Scenarios

### Scenario 1 — Cheap-Model Routing

A tool-enabled HR request already has an authoritative leave-balance result and only requires response formatting.

Expected concept:

```text
low reasoning requirement
→ economy-capable eligible model
```

### Scenario 2 — Complex Reasoning

A high-risk policy interpretation requires stronger reasoning capability.

Expected concept:

```text
advanced reasoning requirement
→ frontier-quality eligible model
```

### Scenario 3 — Hard Residency Constraint

An EU-sensitive request must be routed only to EU-approved models.

Failover must remain inside the compliant eligible set.

### Scenario 4 — Provider Outage

The selected provider becomes unavailable.

The circuit breaker opens and the gateway re-evaluates remaining eligible candidates without requiring provider-specific changes in the upstream application.

### Scenario 5 — Safe Cache Reuse

A repeated organizational policy question with equivalent policy version and security scope is served from cache.

An employee-specific/tool-derived request is not globally reused.

### Scenario 6 — No Eligible Model

A request requires a combination such as:

```text
EU residency
+ tool calling
+ very large context
```

and no configured model satisfies every hard constraint.

Expected behavior:

```text
controlled rejection
```

not "pick the closest model anyway."

---

## 27. Evaluation Strategy

Pattern 04 should produce measurable evidence across areas such as:

- correct task-to-capability resolution
- routing-policy accuracy on a deterministic scenario set
- hard-constraint violation rate (target: zero)
- model-eligibility correctness
- provider failover success rate
- failover policy compliance
- retry count and retry-storm prevention
- cache-hit rate
- unsafe cache-reuse prevention
- p50/p95/p99 gateway latency overhead
- per-team/model/provider cost attribution
- model-routing distribution
- provider health/circuit-breaker transitions
- provider-normalization compatibility for structured outputs/tool semantics where implemented

The goal is not simply to prove that the gateway can forward requests.

The goal is to prove that it makes controlled, explainable, policy-compliant routing decisions.

---

## 28. Failure Modes to Teach

Pattern 04 should explicitly discuss and where practical test:

- provider timeout
- provider HTTP 429
- provider 5xx outage
- regional provider outage
- circuit breaker open
- no eligible model
- invalid model registry configuration
- unsupported capability
- context window too small
- data-residency conflict
- caller attempts to downgrade risk
- caller supplies untrusted routing metadata
- cache-key collision / unsafe reuse
- stale cached policy response
- cost pricing table changes
- provider response normalization failure
- token-accounting mismatch
- excessive retry/failover loops
- self-hosted endpoint unavailable
- usage-store failure
- telemetry failure without blocking inference where safe

---

## 29. Deliberately Not in Scope

Pattern 04 will not initially attempt to build:

- a full commercial LLM gateway product
- dozens of providers
- production multi-region infrastructure
- automated contract billing/chargeback
- admin-driven live routing-policy editing
- a machine-learned router as the baseline
- reinforcement-learning-based model selection
- production enterprise SSO
- full secrets-management platform
- production compliance certification
- complete semantic equivalence across all provider features
- huge-scale ClickHouse/warehouse telemetry from day one

These may be discussed as design-only production evolution where useful.

---

## 30. Key Architecture Decisions to Capture as ADRs

The eventual implementation should include ADRs covering at least:

1. Why enterprise inference is centralized behind a gateway
2. Why the gateway exposes an OpenAI-compatible API
3. Why hard compliance constraints precede cost/quality optimization
4. Why task profiles resolve to capabilities rather than provider names
5. Why task/risk/model/routing policy is versioned and configuration-driven
6. Why capability tier is separated from hosting class
7. Why provider adapters normalize request/response semantics
8. Why failover re-evaluates eligible candidates instead of selecting the next configured tier
9. Why provider/model health uses circuit breakers
10. Why caching is context-, freshness-, and security-aware
11. Why PostgreSQL is sufficient for initial usage/routing telemetry
12. Why cost accounting records pricing versions
13. Why directly measured telemetry is distinguished from derived quality evaluation
14. Why risk cannot be downgraded by an upstream caller below registered policy minimum
15. Why new business tasks should usually be configuration while new platform capabilities may require code changes

Each ADR should include an Interview Takeaway.

---

## 31. Interview Questions This Pattern Should Support

After completing Pattern 04, the repository should provide concrete evidence for answering questions such as:

### Gateway Architecture

- Why introduce an LLM gateway instead of letting each application call providers directly?
- Why expose an OpenAI-compatible API?
- What does the gateway normalize across providers?
- What should remain outside the gateway?

### Routing

- Who decides data classification?
- Who decides whether a task requires advanced reasoning?
- How should task type and risk be represented?
- How do you add a new business task without modifying routing code?
- When does a new task require a code change rather than configuration?
- Why should task profiles resolve to capabilities instead of model names?

### Governance

- How do you ensure a cheap-model route cannot violate data residency?
- How do you prevent callers from downgrading risk?
- What happens when no model satisfies all hard constraints?
- How do you reconstruct why a model was selected yesterday?

### Reliability

- Where do you place circuit breakers?
- Which failures should retry, fail over, or fail immediately?
- How do you avoid retry storms and runaway cost?
- What does transparent provider failover actually guarantee?

### Cost and Observability

- How do you attribute spend by application/team?
- How do you keep historical cost calculations reproducible when model prices change?
- Which gateway metrics are directly observable and which require evaluation?
- When would PostgreSQL stop being sufficient for usage analytics?

### Caching

- Which LLM responses are safe to cache?
- Why is hashing only the user prompt unsafe?
- How do policy versions and security scope affect cache keys?

### Enterprise Evolution

- When should self-hosted models be introduced?
- Why is self-hosted a deployment characteristic rather than a capability tier?
- How would the routing strategy evolve from deterministic policy to a learned router?

---

## 32. Portfolio Story

The first four patterns form a coherent progression:

```text
Pattern 01 — KNOW
Corrective RAG
"What evidence should I trust?"

        ↓

Pattern 02 — REMEMBER
Enterprise AI Memory
"What context should I retain?"

        ↓

Pattern 03 — ACT
Tool Calling & MCP
"What external capability may I invoke?"

        ↓

Pattern 04 — ROUTE
LLM Gateway & Intelligent Model Routing
"Which model/provider should execute this inference, under what constraints?"
```

Pattern 04 turns the preceding application-level capabilities into a platform-level concern and demonstrates how multiple AI applications can share model governance without sharing provider-specific implementation code.

---

## 33. Frozen Pattern Definition

### Pattern

**Pattern 04 — Designing an Enterprise LLM Gateway & Intelligent Model Routing**

### Use Case

**Enterprise-wide LLM Gateway serving multiple AI assistants and services**

### Core Thesis

> Build a shared inference gateway that exposes a provider-neutral/OpenAI-compatible surface and centrally enforces model eligibility, compliance and residency constraints, task- and risk-aware routing, provider failover, context-aware caching, usage metering, cost attribution, and operational observability while keeping upstream application code independent of individual model providers.

### Frozen Architectural Principles

- hard constraints first, optimization second
- upstream applications declare trusted business/security context; gateway enforces it
- task complexity is a routing concern, not a security classifier
- task/risk/model/routing policy is versioned and configuration-driven
- task profiles resolve to capabilities, not provider names
- business tasks should usually be addable through configuration
- new platform capabilities may require code changes to extend the capability model
- upstream callers cannot downgrade below registered minimum risk/policy
- model capability tier and hosting class are separate dimensions
- failover always preserves hard constraints
- provider adapters normalize provider-specific semantics
- caching is context-, freshness-, and security-aware
- cost, token use, latency, errors, retries, and cache behavior are directly measurable
- quality is derived/evaluated separately and must record provenance
- pricing versions are preserved for historical cost reproducibility
- the gateway is service-to-service infrastructure; the admin dashboard is an operational surface
- PostgreSQL is the initial usage/routing store; specialized analytics infrastructure is introduced only when evidence justifies it

### Candidate Scenarios

1. Cheap-model routing for authoritative tool-result formatting
2. Frontier-quality routing for high-risk complex reasoning
3. Hard EU residency constraint
4. Provider outage with compliant failover
5. Safe context-aware cache reuse
6. Controlled rejection when no eligible model exists

### Status

**FROZEN — Approved as Pattern 04 planning baseline.**

Detailed implementation passes, exact provider models, self-hosted runtime choice, policy-file format, routing scoring formula, cache-key implementation, load-test tool, and dashboard implementation remain intentionally deferred to the dedicated Pattern 04 build thread.
