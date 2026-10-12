# TECH_SPEC.md — Pattern 13: Decision-Native AI Architecture

**Status:** DESIGNED · 2026-10-12  
**Pattern principle:** Probabilistic Judgement, Deterministic Authority

## 1. Problem statement and decision boundary

We need typed, uncertainty-aware semantic judgements without allowing model output to become authorization or business policy. The system can choose a model based on evidence and operational constraints, but every candidate must feed the same explicit application contract. A decision-model family is **an implementation choice**, not itself the architectural pattern.

## 2. Minimal contracts (conceptual, language-neutral)

```text
DecisionRequest
  requestId, sanitizedState, questionSetVersion, questions[]
  requesterContextReference, policyContextVersion

TypedQuestion
  id, type: CHOICE | ORDINAL | BINARY
  allowedOptions / levels, descriptions, version

Judgement
  questionId, selectedValue, probabilities?, probabilityKind
  status: VALID | UNAVAILABLE | MALFORMED | UNSUPPORTED
  modelProvider, modelRevision, adapterVersion

DecisionEvaluation
  judgements[], latency, tokenOrComputeUsage, calibrationVersion?
  provenance, errorCategory?

PolicyDecision
  outcome: ROUTE | HUMAN_TRIAGE | RESTRICTED_REVIEW | QUARANTINE
  ruleId, reasonCode, policyVersion, questionSetVersion
  modelRevision, auditId
```

`probabilityKind` must distinguish native model probability, calibrated score and unavailable/non-comparable estimate. Do not invent a probability when a provider only returns a label. Decision policy may decline to automate if comparable confidence evidence is absent.

### Provider port

```text
IDecisionModel.evaluate(DecisionRequest) -> DecisionEvaluation
```

A concrete adapter owns network/local runtime SDKs, authentication, schema translation, timeouts, retries and version metadata. Policy reads only normalized results. A fake model implements this port for deterministic unit tests.

## 3. Ordered processing flow

1. Authenticate/authorize the caller and minimize sensitive input before remote inference.
2. Validate a versioned question contract and request size.
3. Evaluate through a selected adapter, keeping any unsupported capabilities explicit.
4. Validate result completeness, label membership and probabilities (finite values, valid ranges and distributions where applicable).
5. Apply the **matching model/revision-specific** calibration version and selective-automation thresholds; treat domain shift as a reassessment trigger.
6. Apply independently authoritative ordered policy and permission checks.
7. Execute only permitted actions, otherwise abstain or send to human review.
8. Persist a privacy-safe, reconstructible audit record and capture later human overrides as evaluation feedback (not automatic retraining truth).

## 4. Example policy priorities (illustrative, not production thresholds)

```text
IF provider_failed OR judgement_invalid -> HUMAN_TRIAGE
ELSE IF hard_block_policy -> RESTRICTED_REVIEW
ELSE IF injection_risk_above_validated_threshold -> QUARANTINE / review
ELSE IF sensitive_risk_above_validated_threshold -> RESTRICTED_REVIEW
ELSE IF human_needed OR uncertainty_high -> HUMAN_TRIAGE
ELSE IF classification_is_allowed AND authority_valid -> ROUTE
ELSE -> HUMAN_TRIAGE
```

Human safety or sensitive escalations take precedence over route confidence. An inference score never waives a permission check. Review whether quarantine is appropriate for the domain (some suspected injections may be ordinary quoted text).

## 5. Evaluation contract

Use frozen development/calibration/test splits. Tune wording and model candidates on dev; fit candidate-specific calibration and thresholds on calibration; reserve test for unbiased comparison. Compare:

- queue/category macro-F1, strict accuracy and confusion matrices;
- accuracy **at auto-route coverage**, plus abstention and referral rates;
- sensitive/injection precision, recall and missed-positive review;
- Expected Calibration Error, reliability curves and probability stability **only where confidence semantics permit**;
- urgency ordinal error and cost of incorrect escalation;
- option-order, punctuation/paraphrase and code-mixed/noisy robustness;
- provider failures, malformed results, latency p50/p95/p99, cold starts and throughput;
- API billing versus local hardware/hosting/operations **total cost of ownership**;
- privacy, data residency, model/version pinning, support and rollback risk.

Report metric denominators and uncertainty; small synthetic data does not establish rare-event production safety. Define acceptance thresholds prospectively and report misses. Model selection may legitimately conclude **none passes**.

## 6. Failure and negative-test matrix

| Scenario | Expected behavior |
|---|---|
| Timeout or provider outage | No auto-action; human fallback |
| Invalid label / partial question set | Reject judgement and escalate |
| NaN, negative, out-of-range probability | Reject/abstain, log sanitized reason |
| Strong queue score + sensitive signal | Sensitive policy precedence wins |
| Unauthenticated/unauthorized action | Authorization denies regardless of model |
| Choice order changes | Match stable IDs; record decision flips |
| Confidence drift after model update | Recalibrate and gate release |
| Prompt injection inside ticket | Treat input as data; never follow instructions |
| Provider swap | Policy behavior invariant for equivalent normalized judgements |
| Missing human-review queue / audit sink | Defined safe degradation; no silent auto-route |

## 7. Architectural trade-offs

- **Rules only:** first choice for explicit low-variance rules; cannot generalize well to nuanced language.
- **Supervised ML / embeddings:** strong where representative labeled data and retraining lifecycle are available.
- **Decision-native models:** appealing for bounded typed choices with meaningful uncertainty, but require vendor/runtime and probability validation.
- **Generative structured-output LLM:** useful for broader reasoning or generation, but JSON schema and self-reported confidence do not establish calibration.
- **Human review:** remains the safe default where meaningful automated confidence or required authority cannot be established.

Do not infer model superiority from release benchmarks. Keep model-specific implementation and empirical comparisons in the consuming project.

## 8. Reference implementation and separation of ownership

**Pattern repo:** defines reusable architecture, illustrative contracts, deterministic fake-adapter demonstrations, and evaluation/verification rules.

**[Governed Intake Router portfolio project](https://github.com/midhiman-dev/portfolio-knowledge-base/blob/main/projects/governed-intake-router-jev.md):** owns Jev, Vela 2.0, Microsoft-Decision-1 and structured LLM adapter implementation plans, full business question definitions, provider trade-offs, golden dataset and eventual empirical evidence.

## 9. Implementation evidence gate

At present **DESIGNED**. The README and specification are architecture records, not runtime proof. To promote to VERIFIED, include executable source, a repeatable test command, passing positive and negative results, versioned audit examples, and an evidence report with known limitations.
