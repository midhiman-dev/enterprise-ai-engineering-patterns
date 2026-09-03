# Model Configuration Changelog

This file records meaningful changes to the CRAG generation model or its behaviour-affecting parameters.

## crag-generation v1.0.0 — 2026-09-03

**Status:** Active

**Purpose**

Establish a governed baseline for the model configuration currently used by CRAG.

**Current baseline**

- Provider: `groq`
- Default model: `openai/gpt-oss-120b`
- Temperature: `0.0`
- Runtime model override: `GROQ_MODEL`
- Runtime source: `src/corrective_rag/infrastructure/generation/groq_config.py`

**Why this matters**

CRAG behaviour can change even when application code and prompts stay unchanged. Changing the model or a behaviour-affecting parameter therefore needs the same basic discipline: record the change, review it, test it, and keep rollback possible.

**Verification**

This entry records the existing runtime configuration as the initial governed baseline. It does not claim that a model comparison or parameter experiment was performed for v1.0.0.

Future model or parameter changes should be evaluated against `crag-regression-suite` and any relevant security tests before the new version is accepted.

## Change rule

For future model configuration versions, record:

- previous model/configuration
- new model/configuration
- why it changed
- expected improvement
- possible regression or risk
- evaluations run
- relevant quality, safety, latency, or cost observations
- acceptance or rollback decision
