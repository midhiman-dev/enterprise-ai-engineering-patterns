# Pattern 6 — Designing LLM Evaluation for Production AI Systems

## Status

**Initial architecture plan — frozen before implementation starts.**

This document captures the intended scope, architecture, evaluation philosophy, benchmark strategy, release-gate design, governance requirements, human-review model, and relationship to Pattern 5.

---

# 1. Why This Pattern Exists

One of the most common lines in an AI team's standup is:

> "The new prompt looks better."

Looks better to whom? Compared to what? Measured how?

That is not evaluation. That is a vibe.

AI systems change constantly through:

- prompt edits;
- model swaps;
- parameter changes;
- retrieval changes;
- chunking changes;
- tool-selection logic changes;
- routing-rule changes;
- policy and guardrail changes.

A production team needs more than subjective inspection before those changes are released.

The core architecture principle for this pattern is:

> **AI behaviour changes must pass repeatable, versioned evidence gates before deployment.**

---

# 2. Pattern 5 vs Pattern 6

Pattern 5 and Pattern 6 solve different problems.

**Pattern 5 — AI Observability** asks:

> Is the deployed system behaving correctly right now in production?

**Pattern 6 — AI Evaluation** asks:

> Is this proposed change safe and valuable enough to ship at all?

Together they form a closed production quality loop:

```text
                  BUILD
                    │
                    ▼
              Change proposed
                    │
                    ▼
              ┌────────────┐
              │ Pattern 6  │
              │ Evaluation │
              └──────┬─────┘
                     │ PASS
                     ▼
                  Deploy
                     │
                     ▼
              ┌────────────┐
              │ Pattern 5  │
              │Observability│
              └──────┬─────┘
                     │
                failure / drift
                     │
                     ▼
                Human review
                     │
                     ▼
            New benchmark case
                     │
                     └───────────────┐
                                     │
                                     ▼
                                Pattern 6
```

The long-term operating principle is:

> **Production failures discovered by observability should strengthen future pre-release evaluation.**

---

# 3. Reference Use Case

## Enterprise AI Evaluation Harness

Build one shared evaluation harness across the AI systems introduced in Patterns 1–4.

The architecture should use:

- one common evaluation runner;
- one common evaluation result model;
- one common judge-calibration process;
- one common release-gate mechanism;
- one human-review workflow;
- separate benchmark datasets and correctness rules for each AI system.

The evaluation mechanics are shared.

The definition of correctness remains application-specific.

```text
                  Shared Evaluation Harness

                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     Benchmark       Evaluation       Release Gate
      Runner           Engine
          │
    ┌─────┼─────────────┬──────────────┐
    ▼     ▼             ▼              ▼
  CRAG   Memory       MCP Agent      Gateway
 dataset  dataset       dataset        dataset
```

Do not create four independent evaluation frameworks.

---

# 4. What an Evaluation Pipeline Is

An evaluation pipeline is the quality gate a prompt, model, retrieval, routing, or agent change must pass before it is allowed into production.

It is closer to a test suite than a dashboard.

The target operating model is:

```text
Pull Request
     │
     ▼
Unit Tests
     │
     ▼
Integration Tests
     │
     ▼
AI Evaluation Suite
     │
     ├── quality
     ├── regression
     ├── cost
     └── latency
     │
     ▼
Release Policy
     │
 ┌───┴────┐
 │        │
PASS     FAIL
 │        │
Merge    Block
```

A meaningful prompt or model change must not bypass evaluation simply because the code diff is small.

---

# 5. Core Evaluation Pillars

## 5.1 Offline Benchmark Datasets

Each AI system must have a fixed, versioned benchmark dataset.

The benchmark should contain:

- real or realistic historical queries;
- expected evidence or expected behaviour;
- adversarial cases;
- edge cases;
- known past failures;
- held-out cases not used during prompt tuning;
- regression cases that must never silently break again.

A benchmark dataset creates the fixed comparison point required to answer:

> Is this change actually better than the current baseline?

### Initial benchmark size

The reference implementation does not need thousands of examples.

Start with approximately **20–30 deliberate cases per system**.

Example initial scale:

```text
CRAG                  25
HR Memory             25
MCP Agent             25
Gateway Routing       25
                     ───
~100 benchmark cases
```

Quality of cases matters more than volume.

Suggested categories:

```text
normal
boundary
ambiguous
known regression
adversarial
insufficient evidence
failure/recovery
```

Every real production failure discovered later should become a candidate regression case.

---

## 5.2 Regression Tests in CI/CD

Prompt, model, retrieval, memory, agent, and routing changes should run the benchmark suite automatically.

The pipeline should capture:

- quality score;
- regression failures;
- cost;
- latency;
- commit SHA;
- benchmark version;
- prompt/model/configuration versions;
- evaluator version.

The score history should remain traceable so slow degradation across commits is visible even when no single run crosses a hard threshold.

Design principle:

> **If a known failure was fixed once, that failure should remain permanently tested.**

---

## 5.3 LLM-as-a-Judge, Done Properly

LLM-based evaluation can be useful for semantic dimensions such as:

- correctness;
- groundedness;
- completeness;
- evidence use;
- answer relevance;
- policy adherence.

But an LLM judge must not be treated as ground truth.

### Rubric design

Do not ask only:

```text
quality: 1–5
```

Score explicit dimensions independently against explicit criteria.

Example:

```text
correctness
3 — materially wrong
4 — mostly correct with minor omission
5 — correct and complete for the expected scope


groundedness
3 — significant unsupported claims
4 — mostly supported with minor unsupported content
5 — all material claims supported by admitted evidence
```

### Judge calibration

Before trusting a judge:

1. prepare human-labeled calibration cases;
2. run the judge on the same cases;
3. compare judge ratings against human ratings;
4. measure agreement;
5. improve the rubric or judge prompt if agreement is poor.

```text
Human-labeled calibration cases
           │
           ▼
        Judge
           │
           ▼
Compare judge labels
against human labels
           │
           ▼
Agreement acceptable?
       /       \
     no         yes
     │           │
 recalibrate    use judge
```

### Re-calibration rule

Re-calibrate whenever any of the following changes:

- judge model;
- judge prompt;
- rubric;
- judge model configuration.

A newer judge model is not automatically a better judge for the application's evaluation task.

### Judge output

Do not require hidden chain-of-thought.

Require concise, inspectable rubric justification or evidence.

Example:

```json
{
  "groundedness": 4,
  "correctness": 5,
  "completeness": 3,
  "evidence": [
    "The answer correctly uses the retrieved leave policy.",
    "It omits the documented probation exception."
  ]
}
```

A bare score such as `4.2/5` is not sufficient for debugging.

---

## 5.4 Human Review for High-Stakes Outputs

Automated evaluation scales, but it must not become the only gate for workflows where mistakes carry real consequences.

Use policy-defined human review.

Examples:

```text
ordinary FAQ
→ sampled human review

low-confidence policy answer
→ human review / escalation

consequential financial or legal action
→ human approval may be mandatory before action
```

Human labels should feed back into:

- benchmark datasets;
- calibration datasets;
- regression cases;
- rubric improvements.

Disagreement between human reviewers and the judge is itself an evaluation signal.

Track where practical:

```text
judge agreement rate
human override rate
false positive rate
false negative rate
disagreement by rubric dimension
```

A spike in judge-human disagreement may indicate:

- judge drift;
- ambiguous rubric wording;
- inconsistent human labeling;
- a new production behaviour class;
- evaluator misalignment.

---

# 6. Benchmark Design Principle

## Expected Behaviour, Not Always Expected Text

Do not reduce every evaluation case to exact-string answer matching.

Bad benchmark shape:

```json
{
  "question": "...",
  "expected_answer": "one exact paragraph"
}
```

Prefer benchmark cases that describe behaviour:

```text
Input
Expected evidence
Expected decisions
Expected constraints
Expected outcome
Evaluation rubric
```

Different systems require different definitions of correctness.

---

# 7. Benchmark 1 — CRAG

## What is evaluated

CRAG evaluation should focus on retrieval and grounded generation.

Example benchmark case:

```yaml
id: crag-017
question: Why is my Kubernetes pod repeatedly restarting?

expected_sources:
  - pod-lifecycle
  - crashloopbackoff

expected_route:
  - retrieve
  - grade_documents
  - generate
  - hallucination_check
```

Potential dimensions:

```text
retrieval precision
retrieval recall
evidence relevance
groundedness
answer correctness
safe refusal
latency
cost
```

### Regression example

```text
Chunking strategy changed
        ↓
Same benchmark
        ↓
Retrieval precision

0.91 → 0.76

        ↓
RELEASE BLOCKED
```

The purpose is to detect silent quality regressions caused by retrieval or grading changes before deployment.

---

# 8. Benchmark 2 — HR Memory Assistant

The HR Memory Assistant is especially useful because correctness is not simply answer similarity.

Example case:

```text
Question:
"What leave balance did I carry forward?"

Expected behaviour:
- retrieve relevant episodic employee memory;
- do not substitute generic policy;
- respect employee authorization;
```

Another case:

```text
Question:
"What is the current parental leave policy?"

Expected behaviour:
- use current semantic/policy knowledge;
- reject stale remembered policy;
- surface uncertainty when evidence is insufficient.
```

Evaluation dimensions may include:

```text
answer correctness
memory-tier selection
freshness behaviour
authorization behaviour
grounding
human escalation behaviour
```

This is also the strongest example for policy-defined human review because a wrong HR policy or approval-chain answer can have real employee consequences.

---

# 9. Benchmark 3 — Order Support MCP Agent

Agent evaluation must evaluate execution trajectories, not just final prose.

Example customer request:

```text
"My order hasn't arrived and I'd like a refund."
```

Expected trajectory might be:

```text
lookup_order
      ↓
check_delivery_status
      ↓
determine_refund_eligibility
      ↓
request_human_approval
      ↓
refund only after approval
```

Evaluation questions:

```text
Was the correct tool selected?
Was tool ordering correct?
Was an unnecessary tool called?
Was human approval preserved?
Was an irreversible action attempted prematurely?
Was tool failure handled correctly?
```

Critical principle:

> **A perfectly worded final answer can hide an incorrect agent execution path.**

Therefore Pattern 6 must evaluate both response quality and agent behaviour.

---

# 10. Benchmark 4 — LLM Gateway

The LLM Gateway provides a deterministic classification-style benchmark.

Example:

```yaml
request: "What is our annual leave policy?"
expected_tier: fast
```

Versus:

```yaml
request: >
  Compare three architecture alternatives,
  identify failure modes, and recommend one.
expected_tier: frontier
```

Evaluation dimensions:

```text
routing accuracy
false frontier routing
false cheap-tier routing
latency
cost
fallback behaviour
```

Example trade-off:

```text
Quality:  94% → 95%
Cost:     $0.04 → $0.17
```

This is not automatically a successful change.

---

# 11. Multi-Objective Evaluation

Evaluation should consider quality, cost, and latency together.

Example:

| Candidate | Quality | Cost | p95 latency |
|---|---:|---:|---:|
| Current | 91% | $0.06 | 850ms |
| A | 94% | $0.07 | 910ms |
| B | 95% | $0.24 | 2.6s |

Candidate B is not automatically the best choice simply because it has the highest quality score.

A reasonable architecture decision may be:

> Candidate A gives the strongest quality improvement while staying within accepted operational constraints.

The evaluation harness should therefore support several gate types.

### Hard requirements

Examples:

```text
refund without approval = 0 tolerance
wrong authorization behaviour = 0 tolerance
known critical regression failures = 0 tolerance
```

### Threshold requirements

Examples:

```text
groundedness >= 0.90
routing accuracy >= 0.95
```

### Relative-comparison requirements

Examples:

```text
quality must not decrease by more than 2%
cost must not increase by more than 15%
p95 latency must not regress by more than 20%
```

The release gate is therefore a **policy**, not one magic score.

---

# 12. Dataset Separation

The reference design should distinguish at least four dataset purposes.

```text
Development Set
      │
      └─ engineers may inspect and tune against

Regression Set
      │
      └─ known behaviour that must remain stable

Holdout Set
      │
      └─ not used during prompt tuning

Calibration Set
      │
      └─ human-labeled cases for evaluator validation
```

The reference implementation can keep these datasets small.

The important lesson is the conceptual separation.

Do not evaluate only against the same data used to tune the prompt.

---

# 13. Proposed Architecture

Initial architecture:

```text
                  Change / Pull Request
                         │
                         ▼
              ┌────────────────────┐
              │ Evaluation Runner  │
              └─────────┬──────────┘
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
 Benchmark Store   Evaluation Engine   Cost/Latency
       │                │               Metrics
       │                │
       └────────────────┼─────────────────┘
                        ▼
                 Evaluation Report
                        │
                        ▼
                   Release Gate
                        │
                  PASS / FAIL
```

Parallel human-review path:

```text
Production / flagged cases
          │
          ▼
   Human Review Queue
          │
          ├──► Calibration Dataset
          │
          └──► Regression Dataset
```

---

# 14. Core Components

## Evaluation Runner

Responsibilities:

- load selected benchmark dataset version;
- invoke the target system;
- capture outputs, traces, latency, and cost;
- invoke deterministic and semantic evaluators;
- produce evaluation results.

## Benchmark Store

Responsibilities:

- store versioned datasets;
- preserve regression and holdout separation;
- preserve expected behaviour and rubric metadata;
- keep previous release evidence reproducible.

## Evaluation Engine

Responsibilities:

- deterministic checks;
- retrieval metrics;
- trajectory validation;
- LLM-based semantic scoring;
- judge rationale capture;
- calibration support.

## Release Gate

Responsibilities:

- apply release policy;
- compare candidate vs current baseline;
- enforce zero-tolerance rules;
- evaluate quality/cost/latency thresholds;
- produce a PASS or FAIL decision with evidence.

## Human Review Queue

Responsibilities:

- route policy-selected production samples;
- route flagged and high-risk outputs;
- collect reviewer labels;
- capture judge-human disagreement;
- feed benchmark and calibration datasets.

---

# 15. Domain Model

Initial entities/value objects:

```text
BenchmarkDataset
BenchmarkCase
EvaluationRun
EvaluationResult
EvaluationMetric
ReleaseGate
HumanReview
JudgeCalibration
```

Example `EvaluationRun` shape:

```text
EvaluationRun
 ├── run_id
 ├── system_id
 ├── commit_sha
 ├── dataset_version
 ├── prompt_version
 ├── model_config_version
 ├── evaluator_version
 ├── started_at
 └── results
```

Potential ports:

```text
BenchmarkRepository
SystemUnderTest
Evaluator
JudgeEvaluator
HumanReviewRepository
EvaluationResultRepository
ReleaseGatePolicy
CostMeter
LatencyMeter
```

Infrastructure adapters must implement these ports.

The application layer should not import concrete CI providers, LLM SDKs, database libraries, or human-review transport details directly.

---

# 16. Evaluation Governance and Traceability

An evaluation score is meaningless unless the system can reconstruct what was actually evaluated and how.

Where relevant, capture:

```text
application_version
commit_sha
prompt_id
prompt_version
model_config_id
model_config_version

dataset_id
dataset_version

rubric_id
rubric_version

judge_prompt_version
judge_model
judge_config_version

evaluation_code_version
```

This protects against a common failure mode:

> The application did not change, but the evaluator changed — and the team interpreted the score movement as product quality movement.

The evaluator is itself a governed component.

---

# 17. Pattern 5 Feedback Integration

Pattern 5 should supply candidate regression cases into Pattern 6.

Example:

```text
Control Tower detects production failure
        ↓
Operator investigates trace
        ↓
Root cause confirmed
        ↓
Human labels expected behaviour
        ↓
New benchmark case created
        ↓
Regression suite updated
        ↓
Future releases test the case automatically
```

Examples:

- retrieval-quality incident becomes a CRAG benchmark case;
- stale-memory incident becomes an HR benchmark case;
- wrong tool trajectory becomes an MCP regression case;
- misrouted request becomes a Gateway routing case.

This creates a durable quality flywheel.

---

# 18. Initial CI/CD Behaviour

Target workflow:

```text
Prompt / model / retrieval / routing change
        ↓
Pull request
        ↓
Unit + integration tests
        ↓
Pattern 6 evaluation suite
        ↓
Release policy
        ↓
PASS ───────────► merge / deploy
FAIL ───────────► block + evaluation report
```

The implementation should eventually record evaluation trends per commit.

However, CI enforcement should only be claimed as implemented after actual pipeline wiring exists.

---

# 19. Planned ADRs

Create ADRs as decisions are implemented rather than retroactively inventing them.

Initial ADR backlog:

## ADR-001 — Shared Evaluation Harness with Per-System Benchmark Datasets

Why evaluation mechanics are shared while correctness remains system-specific.

## ADR-002 — Versioned Fixed Benchmark Datasets for Regression Comparison

Why stable datasets are required for meaningful comparison over time.

## ADR-003 — Multi-Dimensional Release Gates Covering Quality, Latency and Cost

Why the system should not optimize only a single quality score.

## ADR-004 — Calibrated LLM-as-a-Judge Evaluation

Why LLM judges must be validated against human-labelled cases and re-calibrated when the evaluator changes.

## ADR-005 — Human Review and Production-Failure Feedback into Benchmark Datasets

Why human labels and production failures should close the evaluation loop.

## Potential ADR-006 — CI Enforcement of AI Evaluation Gates

Create only when the CI mechanism is implemented and verified.

---

# 20. Deliberate Non-Goals

Pattern 6 is not intended to become:

- an ML training platform;
- a generic model leaderboard;
- a synthetic-data generation platform;
- a replacement for domain experts;
- a claim that LLM-as-judge establishes objective truth;
- a large proprietary evaluation framework;
- a replacement for production observability;
- a replacement for normal unit and integration testing.

The portfolio thesis is intentionally narrower:

> **Build a small, reproducible enterprise evaluation harness that determines whether changes to AI behaviour are safe enough to release.**

---

# 21. Design Principles

1. **Every meaningful AI behaviour change runs against a fixed benchmark before release.**
2. **Known critical regressions can block a release just like failed software tests.**
3. **Benchmark datasets are versioned and reproducible.**
4. **Do not evaluate only on data used to tune the prompt.**
5. **Evaluate expected behaviour, not only exact answer text.**
6. **Agent trajectories and tool decisions are part of correctness.**
7. **LLM judges are calibrated against humans before being trusted.**
8. **Judge/model/rubric changes require re-calibration.**
9. **Quality, cost, and latency must be evaluated together.**
10. **High-risk workflows retain policy-defined human review or approval.**
11. **Judge-human disagreement is a useful quality signal.**
12. **Production failures should become regression tests.**
13. **Evaluation artifacts and evaluator versions must be traceable.**
14. **Do not claim controls or CI gates that have not actually been implemented.**

---

# 22. Common Failure Modes the Pattern Should Demonstrate

The tutorial and demo should explicitly show why these practices matter.

## Failure: prompt tuned against its own benchmark

Result:

- impressive score;
- weak generalization;
- false confidence.

## Failure: prompt change bypasses CI evaluation

Result:

- regression reaches production;
- issue discovered only through Pattern 5.

## Failure: uncalibrated LLM judge

Result:

- inconsistent scores;
- disagreement with domain reviewers;
- misleading release decisions.

## Failure: judge returns only a number

Result:

- no useful evidence for debugging.

## Failure: quality improves while cost explodes

Result:

- technically better answers;
- economically worse system.

## Failure: only user complaints become review samples

Result:

- evaluation happens after harm rather than before or during controlled review.

---

# 23. Human Mental Model

The portfolio owner should eventually be able to explain Pattern 6 without reconstructing it from the repository.

Target explanation:

> "AI changes cannot be reviewed only by reading a prompt and deciding that the output looks better.
>
> Pattern 6 creates a shared evaluation harness. Each AI system owns a versioned benchmark describing what correct behaviour means for that system. CRAG measures retrieval and grounding, the memory assistant tests memory and freshness behaviour, the MCP agent evaluates tool trajectories and approval boundaries, and the Gateway evaluates routing.
>
> Every significant prompt, model, retrieval or routing change runs these cases automatically. Release policy evaluates quality together with latency and cost.
>
> We can use an LLM judge for semantic dimensions, but the judge is first calibrated against human-labelled examples and re-calibrated whenever its model, prompt or rubric changes. High-risk workflows retain human review.
>
> After deployment, Pattern 5 watches production. Real failures found there become new Pattern 6 regression cases. Production experience therefore continuously strengthens the pre-release quality gate."

---

# 24. Pattern-Series Progression

```text
Pattern 1 — Corrective RAG
        ↓
Pattern 2 — Enterprise AI Memory
        ↓
Pattern 3 — Tool Calling / MCP
        ↓
Pattern 4 — LLM Gateway & Routing
        ↓
Pattern 5 — Production AI Observability
        ↓
Pattern 6 — AI Evaluation & Release Gates
```

Pattern 5 asks:

> **What is happening in production?**

Pattern 6 asks:

> **Should this change ship?**

Together they answer a broader enterprise question:

> **How do we continuously improve an AI system without losing control of its quality?**

---

# 25. Initial Delivery Sequence

Implementation should proceed in a disciplined order:

```text
1. Freeze scope and benchmark semantics
        ↓
2. Define domain entities and ports
        ↓
3. Create small versioned datasets for Patterns 1–4
        ↓
4. Implement deterministic evaluators first
        ↓
5. Add LLM judge with explicit rubric
        ↓
6. Add judge calibration against human labels
        ↓
7. Add quality / cost / latency release policy
        ↓
8. Produce evaluation reports
        ↓
9. Wire CI gate only after local behaviour is verified
        ↓
10. Add human-review feedback loop
        ↓
11. Connect production failures from Pattern 5
        ↓
12. Add ADRs, tutorial, verification evidence, and Human Mental Model
```

Do not begin by building a large UI or general-purpose eval platform.

The smallest complete implementation should prove the quality-gate lifecycle first.

---

# 26. North-Star Principle

> **Evaluation is not the thing an AI team does before a major launch. It is the engineering mechanism that decides whether today's prompt, model, retrieval, or agent change is allowed to reach a user at all.**
