# Pattern 05 — Designing AI Observability for Production Systems

## Initial Plan

**Status:** Proposed / planning baseline  
**Reference use case:** **Enterprise AI Control Tower — one observability plane across the systems built in Patterns 1–4**

---

## 1. Why this pattern exists

Patterns 1–4 focus on building individual AI capabilities. Pattern 5 introduces the production operating layer that observes those systems as a fleet.

The architectural question is no longer:

> Is the API alive?

It becomes:

> **Is the AI system still doing the right thing, using the right evidence and tools, at an acceptable cost, for real users?**

Traditional application monitoring can show:

```text
CPU        healthy
Memory     healthy
HTTP       200
Latency    420 ms
Database   reachable

Everything looks fine.
```

while AI behaviour is quietly degrading:

```text
Retrieval precision       ↓
Tool failures             ↑
Frontier-model routing    ↑
Cost/workflow             ↑
Regenerate rate           ↑
Task completion           ↓
```

The core lesson of the pattern is therefore:

> **Availability is not AI correctness.**

A useful mental model is:

```text
System Health
     ≠
AI Behaviour Health
     ≠
Business Outcome Health
```

A production AI observability architecture must connect all three.

---

## 2. Reference scenario — Enterprise AI Control Tower

The Control Tower provides one observability plane across the systems built in Patterns 1–4, including:

- the HR service-desk / knowledge assistant;
- the order-support agent;
- the OMS MCP server used by the order-support agent;
- the LLM Gateway routing workloads between model tiers.

The enterprise pain is simple: once several AI systems are running in production, answering **“is it working?”** cannot rely on uptime alone. Every service may return HTTP 200 with acceptable latency while retrieval quality, tool execution, model routing, cost efficiency, or user outcomes deteriorate silently.

The Control Tower is intended to detect these degradations before users raise support tickets.

---

## 3. Four production failure scenarios

The pattern will demonstrate four failure classes.

### Scenario 1 — Retrieval quality regression

The HR team refreshes its leave-policy documents. Chunk boundaries change and retrieval quality quietly drops.

```text
Policy documents refreshed
        ↓
Chunking changes
        ↓
Retrieval quality drops
        ↓
LLM still answers fluently
        ↓
HTTP 200
        ↓
Wrong answer eventually reaches employee
```

Without AI-specific observability, the system appears healthy.

Relevant metrics may include:

```text
retrieval_precision
retrieval_relevance
evidence_coverage
grounded_answer_rate
```

The Control Tower should detect the quality drop on the same day rather than waiting for an employee to report a subtly wrong policy answer.

This scenario links directly back to the retrieval and Corrective RAG patterns.

---

### Scenario 2 — Agent tool failure

The order-support assistant's custom OMS MCP server starts timing out under load.

Without tool-level tracing, the incident looks like:

```text
Order assistant
      ↓
"Bot seems slow"
```

With layered tracing, an operator can see something closer to:

```text
Trace 91AF...
   │
   ├── intent = order_status
   │
   ├── tool_selected = check_inventory
   │
   ├── tool_latency = 4.8s
   │
   ├── tool_status = timeout
   │
   ├── retry_count = 2
   │
   └── workflow_result = degraded
```

If `check_inventory` is failing on 12% of calls, the operations team knows exactly which dependency is failing.

Architectural principle:

> **Trace decisions and dependencies, not just responses.**

---

### Scenario 3 — Cost spike from a routing bug

A routing-rule change misclassifies simple HR questions as complex reasoning tasks and silently sends them to the frontier model tier.

```text
Simple HR request
      ↓
Classifier / routing rule
      ↓
Wrong complexity classification
      ↓
Frontier tier
      ↓
Correct answer
      ↓
No functional failure
      ↓
2× cost
```

The application still returns correct answers, so ordinary functional monitoring may detect nothing.

Useful cost signals include:

```text
cost/request
cost/workflow
cost/completed-workflow
routing-tier distribution
```

`cost/request` is useful, but `cost/successful-task` or `cost/completed-workflow` is more meaningful because it connects technical spend to business outcome.

---

### Scenario 4 — Silent quality drop after a deployment

A new model is introduced into the Fast & Cheap tier. It passed pre-deployment benchmark evaluation, but production users start hitting **regenerate** much more often.

This demonstrates an important distinction:

> **Offline evaluation and production evaluation answer different questions.**

A model may perform well on a benchmark and still perform poorly for real users.

`regenerate_rate` should be treated as a useful UX proxy rather than as task completion itself.

Where deterministic workflow outcomes can be observed, measure them directly, for example:

```text
HR question
→ answer accepted without escalation
```

or:

```text
Order-support workflow
→ requested order action successfully completed
```

Then correlate signals such as:

```text
regenerate_rate ↑
escalation_rate ↑
task_completion ↓
```

---

## 4. Core design principles

Pattern 5 should demonstrate the following principles explicitly.

### 4.1 Monitor every important layer, not only the LLM

The model is only one component of an AI system. Observability should cover platform behaviour, model behaviour, retrieval/context, tool execution, agent decisions, and user/business outcomes.

### 4.2 Record execution evidence, not only the final answer

Logs and traces should capture relevant retrieval decisions, routing decisions, model configuration, tool calls, retries, fallbacks, evaluations, policy decisions, and workflow outcomes.

### 4.3 Alert on deviations before users file tickets

The Control Tower should identify meaningful deviations from expected behaviour rather than waiting for a support incident.

### 4.4 Evaluate against production traffic

Offline regression suites remain important, but real production traffic reveals behaviour that static benchmark datasets cannot fully reproduce.

### 4.5 Separate ingestion from query workloads

Telemetry ingestion is high-volume and latency-sensitive. Dashboard querying is analytical and read-heavy. These are different workloads and should be architecturally separated.

### 4.6 Prefer outcome-aware metrics

AI metrics become more useful when they connect technical events to completed user or business tasks.

---

## 5. Architectural shape

The architecture deliberately uses separate write and read planes.

### 5.1 Write Plane

```text
AI Systems
   │
   │ OpenTelemetry-compatible traces/events
   ▼
┌─────────────────────────┐
│      Ingestion API      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Ingestion Pipeline    │
│                         │
│ fan-out asynchronously  │
└───────┬────────┬────────┘
        │        │
        │        │
        ▼        ▼
 Event Store    Alert Engine
        │
        └────────────► Evaluation Queue
                            │
                            ▼
                     Evaluation Engine
```

The write plane must add near-zero latency to the originating AI system.

### 5.2 Read Plane

```text
Event Store
   │
   ▼
Metric Aggregation / Materialized Views
   │
   ▼
MetricAggregate / read models
   │
   ▼
┌───────────────────────┐
│      Query API        │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Control Tower UI     │
└───────────────────────┘
```

The dashboard should not issue unrestricted analytical queries directly against raw high-volume telemetry.

The architectural principle is workload separation, not a claim that ClickHouse itself cannot be queried.

The Query API may read from:

- ClickHouse materialized views;
- aggregate tables;
- cached summaries;
- carefully selected trace-detail queries for drill-down.

---

## 6. Proposed technology stack

### Ingestion API

**FastAPI**

The API will be shaped around OpenTelemetry GenAI semantic conventions so that instrumented systems can emit telemetry without requiring a unique custom schema for every team or application.

### Ingestion Pipeline — Application layer

The pipeline fans each accepted event out asynchronously to three responsibilities:

1. persist the event;
2. sample eligible traces into the evaluation queue;
3. check/update alert-related metric streams.

The caller must not wait for evaluation or alert processing.

### Event Store — Infrastructure

**ClickHouse**

Candidate because the expected workload is high-volume, append-oriented telemetry with time-series and analytical aggregation needs.

The final adoption should be validated during implementation rather than treated as unquestionable merely because it is a common observability-store choice.

### Evaluation Engine

An asynchronous worker pool, initially using **Celery or RQ**, periodically samples production traces and runs evaluation jobs.

Possible evaluations include:

- retrieval precision/relevance;
- answer quality;
- groundedness;
- tool-selection correctness;
- policy-conformance checks.

Where useful, evaluation may use an LLM-as-judge, but model-based evaluation is one evidence source rather than ground truth.

### Alert Engine

Watches metric streams for meaningful deviation from expected baselines and routes alerts to adapters such as Slack or PagerDuty.

Example monitored metrics:

- cost per workflow;
- task completion rate;
- retrieval precision;
- tool failure rate;
- routing-tier distribution.

### Query API

**FastAPI**, read-only.

Serves pre-aggregated views and selected trace drill-down information. The dashboard should not depend on raw Event Store queries for normal visualizations.

### Observability Dashboard

**React + TypeScript**

Primary views:

1. model performance;
2. retrieval quality;
3. agent execution;
4. cost;
5. user / business outcome.

The UI also provides trace drill-down showing the full execution path of a selected workflow.

---

## 7. Five observability layers

These layers are the conceptual backbone of the pattern.

### Layer 1 — Platform

Traditional operational telemetry remains necessary:

```text
availability
latency
errors
CPU / memory
queue depth
dependency health
```

### Layer 2 — Model

```text
provider
model
model-config version
latency
tokens
estimated cost
rate limits
retries
fallbacks
refusals
```

### Layer 3 — Context / Retrieval

```text
query / query metadata
retriever
retriever version
document/source identifiers
retrieval scores
evidence coverage
retrieval quality
```

Sensitive raw content should not be logged blindly merely for observability.

### Layer 4 — Agent / Tool Execution

```text
agent decision
tool selected
tool version
tool argument metadata
tool result status
tool latency
retry
fallback
approval
policy decision
```

Raw arguments should be redacted or omitted where they contain sensitive information.

### Layer 5 — User / Business Outcome

```text
task completion
regenerate
escalation
human override
abandonment
workflow success
cost per completed task
```

The overall mental model becomes:

```text
Infrastructure
      ↓
Model
      ↓
Context
      ↓
Agent / Tools
      ↓
User / Business Outcome
```

---

## 8. Domain model

Initial domain entities:

```text
TraceEvent
QualityScore
EvaluationResult
MetricAggregate
Alert
```

### TraceEvent

Represents a normalized telemetry event associated with an AI workflow trace.

### EvaluationResult

Represents the result of one evaluation performed against a trace or trace segment.

Possible shape:

```text
EvaluationResult
 ├── evaluation_id
 ├── trace_id
 ├── evaluator
 ├── evaluator_version
 ├── metric
 ├── score
 ├── rationale
 ├── evaluated_at
 └── evaluation_method
```

This is intentionally distinct from `QualityScore` because the evaluator itself may change over time.

### QualityScore

Represents a normalized quality signal derived from one or more evaluation results or deterministic measurements.

### MetricAggregate

Represents a read-oriented metric aggregate over a defined system, workflow, time period, model, tool, or other supported dimension.

### Alert

Represents a detected operational or quality deviation requiring investigation or escalation.

---

## 9. Domain ports

Initial candidate ports:

```text
EventIngestor
TraceRepository
MetricsRepository
EvaluationQueue
Evaluator
AlertNotifier
```

The Application layer orchestrates ports only.

It should understand concepts such as:

> evaluate this trace

rather than infrastructure instructions such as:

> send a Celery task

Possible Infrastructure adapters include:

```text
ClickHouseTraceRepository
ClickHouseMetricsRepository
CeleryEvaluationQueue
LLMJudgeEvaluator
SlackAlertNotifier
PagerDutyAlertNotifier
```

The same architectural rule used throughout the series applies here:

> **The pipeline must not import ClickHouse, Celery, Slack, PagerDuty, or other vendor SDKs directly. Only adapters should know those technologies.**

---

## 10. Production traceability and governance linkage

Pattern 5 should connect observability to the governance concepts introduced earlier in the series.

Where relevant, a trace should be capable of identifying:

```text
trace_id
system_id
workflow_id

prompt_id
prompt_version

model_config_id
model_config_version

provider
model

policy_version
retriever_version

tool_name
tool_version

deployment_version
```

Not every field is required for every event.

The purpose is to make questions such as the following answerable:

> **What changed immediately before quality deteriorated?**

For example:

```text
Task completion
87% ──────────────┐
                  │
                  ▼
71% ─────────────────────────

                  ▲
                  │
        Fast-tier model
        v3.1 → v3.2
```

Observability therefore becomes connected to prompt governance, model-configuration governance, policy governance, deployment change, and rollback evidence rather than being a collection of disconnected dashboards.

Traceability must not become an excuse to log secrets, sensitive prompts, personally identifiable information, or raw enterprise data unnecessarily.

---

## 11. Evaluation strategy

LLM-as-judge may be useful, but Pattern 5 must not teach the following mental model:

```text
LLM judge says 0.91
       ↓
Truth = 0.91
```

Instead:

```text
Production sample
       ↓
Deterministic metrics where possible
       +
LLM-based evaluation where useful
       +
User behaviour
       +
Periodic human review
       ↓
Quality evidence
```

An LLM judge is an evaluator, not ground truth.

Where model-based evaluation is used, capture evaluator provenance such as:

```text
evaluator_prompt_version
evaluator_model
evaluator_model_config_version
evaluation_schema_version
```

This prevents a change in the observability evaluator from being mistaken for a change in the application under observation.

---

## 12. Alerting model

Alerting should support more than static thresholds.

### Absolute threshold

Example:

```text
cost_per_request > configured_limit
```

### Deviation from baseline

Example:

```text
normal median: 0.07
current median: 0.14
change: +100%
```

Neither value may violate an absolute threshold, but the deviation is operationally significant.

### Rate of change

Useful for quickly emerging failures such as tool timeouts or sudden routing shifts.

### SLO / error-budget breach

Where a workflow has explicit service or quality objectives, alert when those objectives are being consumed or breached.

The first implementation should prefer understandable rolling-baseline comparisons rather than introducing a complex anomaly-detection platform.

---

## 13. Dashboard scope

The UI scope should remain narrow and demonstrable.

### View 1 — Model Performance

```text
Latency
Failure rate
Token usage
Model distribution
Fallbacks
Retries
```

### View 2 — Retrieval Quality

```text
Retrieval relevance
Grounding
Evidence coverage
No-evidence rate
CRAG correction rate
```

### View 3 — Agent Execution

```text
Tool success
Tool latency
Retries
Fallback
Approval frequency
Failed workflow step
```

### View 4 — Cost

```text
Cost/request
Cost/workflow
Cost/completed workflow
Cost by model
Cost by system
Routing-tier distribution
```

### View 5 — User / Outcome

```text
Task completion
Regenerate
Escalation
Human override
Abandonment
User feedback
```

### Trace Explorer

Trace Explorer is a drill-down mechanism rather than a separate monitoring category.

```text
Trace
│
├── request
├── retrieval
├── routing
├── model
├── tool calls
├── policy decisions
├── evaluation
└── outcome
```

It should allow an operator to move from an aggregate deviation to the execution evidence behind representative traces.

---

## 14. Demo design — four controlled incidents

The finished Control Tower should support a repeatable incident-driven demo.

```text
Normal production
        ↓
Incident injected
        ↓
Metric deviation appears
        ↓
Alert generated
        ↓
Operator opens affected metric
        ↓
Trace drill-down
        ↓
Root cause isolated
```

| Incident | Primary signal | Root cause |
|---|---|---|
| HR retrieval regression | Retrieval precision ↓ | Document/chunking change |
| OMS MCP failure | Tool failure ↑ | `check_inventory` timeouts |
| Gateway routing bug | Cost/workflow ↑ | Wrong tier routing |
| Model deployment regression | Completion ↓ / regenerate ↑ | Fast-tier model change |

This incident-driven flow should become the primary portfolio demonstration story.

---

## 15. Initial ADR backlog

The following ADRs should be created early rather than reconstructed after implementation.

### ADR-001 — Separate Telemetry Write and Query Planes

Capture why high-volume ingestion and dashboard analytics are isolated from each other.

### ADR-002 — Adopt OpenTelemetry-Compatible Trace Semantics

Capture why the Control Tower uses vendor-neutral telemetry conventions instead of a unique observability schema per AI application.

### ADR-003 — Use Asynchronous Production Evaluation

Capture why production evaluation must not sit synchronously in the end-user request path.

### ADR-004 — Combine Deterministic, Behavioural and Model-Based Quality Signals

Capture why LLM-as-judge alone is insufficient for production quality assessment.

### Later ADR candidate — ClickHouse Event Store

Create only after validating the actual requirements and implementation trade-offs rather than treating the datastore choice as predetermined.

---

## 16. Deliberate non-goals

Pattern 5 must not become:

- a replacement for Datadog;
- a replacement for Grafana;
- a full OpenTelemetry Collector implementation;
- a generic APM platform;
- an ML anomaly-detection platform;
- a full LangSmith/Langfuse competitor;
- a universal enterprise telemetry platform.

The portfolio thesis is narrower:

> **Show how AI-specific behavioural telemetry can be collected, evaluated, and connected to operational outcomes across multiple enterprise AI systems.**

That is sufficient for the pattern.

---

## 17. Human Mental Model target

After implementation, the human owner should be able to explain the architecture without relying on an AI assistant to reconstruct it.

Target explanation:

> Patterns 1–4 taught us how to build individual AI capabilities. Pattern 5 asks what happens when several of those systems are running in production.
>
> Normal application monitoring tells me whether the service is alive. It does not tell me whether retrieval has degraded, an agent is choosing the wrong tool, my gateway is routing requests to an unnecessarily expensive model, or users have stopped successfully completing their tasks.
>
> The Control Tower therefore collects OpenTelemetry-compatible traces through a high-throughput ingestion path. The pipeline asynchronously stores events, evaluates sampled production traces, and checks operational signals for deviations.
>
> The read path is separate. Aggregated metrics feed dashboards for model performance, retrieval, agent execution, cost, and user outcomes. Operators can then drill from a degraded metric into the complete trace.
>
> The important design principle is that we observe the complete AI workflow—not just the model response—and connect technical telemetry to actual user outcomes.

This explanation should eventually be validated against the implementation and maintained as part of the Human Mental Model evidence for the pattern.

---

## 18. Series progression

Pattern 5 extends the learning progression deliberately:

```text
Pattern 1
Ground the AI

        ↓

Pattern 2
Correct bad retrieval

        ↓

Pattern 3
Let AI interact safely with tools

        ↓

Pattern 4
Route AI workloads intelligently

        ↓

Pattern 5
Observe whether the whole system
is actually behaving correctly
in production
```

The pattern should therefore feel like the operational continuation of the earlier patterns rather than an unrelated observability demo.

---

## 19. Delivery sequence

The current intended delivery sequence is:

```text
Architecture
    ↓
ADRs
    ↓
Implementation
    ↓
Deterministic verification
    ↓
Production-evaluation simulation
    ↓
Human Mental Model
    ↓
Governance evidence
```

The four failure scenarios and five observability layers should be treated as the initial frozen scope unless implementation evidence creates a reason to revisit them.

---

## 20. North-star principle

> **Observe the AI system as a workflow, not the LLM as an isolated component.**

The goal is not to build another dashboard. The goal is to demonstrate how enterprise teams can detect degradation in evidence quality, agent execution, model routing, cost efficiency, and user outcomes before those problems surface as support incidents.
