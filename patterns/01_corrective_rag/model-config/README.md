# Model Configuration Governance

CRAG treats the model and its behaviour-affecting settings as governed configuration.

A model change can alter answer quality, grounding, safety, latency, and cost. A parameter change can also alter behaviour even when the prompt and application code do not change.

## Current configuration

The governed snapshot is `crag-generation.yaml`.

It records:

- configuration ID and version
- provider and model
- behaviour-affecting parameters actually used by CRAG
- reason for the configuration
- evaluation suite used to verify changes
- runtime source of truth

## Change rule

When the model or an important parameter changes:

1. Record what changed and why.
2. Review the change.
3. Run the relevant CRAG regression and security evaluations.
4. Compare behaviour before accepting the new version.
5. Record the decision in `docs/MODEL_CONFIG_CHANGELOG.md`.
6. Keep rollback possible.

Do not record parameters that the application does not actually use merely to make the configuration look complete.

## Runtime note

The runtime source of truth currently remains `src/corrective_rag/infrastructure/generation/groq_config.py`. The governed YAML file documents that active configuration; externalizing runtime configuration into this file would be a separate engineering change.
