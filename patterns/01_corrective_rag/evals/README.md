# CRAG Regression Suite

This folder is the home for prompt-level evaluation records.

The current `crag-system` prompt (`v1.1.0`) is evaluated against the existing CRAG automated tests, including the trust-boundary checks added for indirect prompt injection.

Relevant automated evidence currently includes:

- `tests/unit/infrastructure/generation/test_prompt_injection_boundary.py`
- source trust-boundary tests under the CRAG test suite
- the broader project regression test suite

The prompt metadata uses `evaluated_against: crag-regression-suite` as the stable name for this set of checks.

## Rule for future prompt changes

For each meaningful prompt change:

1. Run the relevant existing tests.
2. Add a new regression case if the change fixes a newly discovered failure mode.
3. Record the reason and verification in `../docs/PROMPT_CHANGELOG.md`.
4. Do not mark a prompt version accepted only because the prompt author or coding agent says it is better.

Prompt changes require evidence, not confidence.
