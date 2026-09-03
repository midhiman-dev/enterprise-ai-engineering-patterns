# Prompt Change Governance

CRAG treats important system prompts like code: changes are versioned, reviewed, tested, and kept rollback-friendly.

## Minimum rules

1. Keep the prompt in Git with a stable `prompt_id` and version.
2. Record why the prompt changed.
3. Review the diff before accepting the change.
4. Run the CRAG regression checks for meaningful prompt changes.
5. Rerun security-focused checks when a prompt change affects trust, permissions, tool use, secrets, or retrieved instructions.
6. Keep enough history to identify which prompt version was active and roll back if behaviour becomes worse.

## Current governed prompt

- Prompt: `corrective-rag-system.md`
- Prompt ID: `crag-system`
- Active version: `1.1.0`
- Evaluation set: `crag-regression-suite`
- Change log: `../docs/PROMPT_CHANGELOG.md`
- Evaluation notes: `../evals/README.md`

## Current implementation note

The runtime system prompt is still defined in `src/corrective_rag/infrastructure/generation/groq_generator.py`. The governed Markdown file mirrors it for review and history. Until prompt loading is externalized, changes must update both places together.
