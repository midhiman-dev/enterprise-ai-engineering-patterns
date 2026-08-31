#!/usr/bin/env python3
"""Learner-readable Golden-Scenario Evaluation Harness for Corrective RAG.

Executes real assembled application end-to-end evaluation against 3 golden scenarios:
  1. Q1_LOCAL_KNOWN: Local / Known query
  2. Q2_STALE_VERSION_SPECIFIC: Stale / Version-Specific post-snapshot query
  3. Q3_FICTIONAL_PREMISE: Fictional feature flag query

Execution mode:
  Opt-in via `--live` CLI flag. Without `--live`, prints a safety message and exits.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from corrective_rag.composition.container import build_application
from corrective_rag.domain.entities.question import Question
from corrective_rag.evaluation.evaluation_models import (
    GoldenEvaluationReport,
    ScenarioResult,
)
from corrective_rag.evaluation.evaluator import (
    extract_scenario_result,
    run_preflight_checks,
)

GOLDEN_SCENARIOS = [
    {
        "scenario_id": "Q1_LOCAL_KNOWN",
        "query": "Why does kubectl get pods show CrashLoopBackOff?",
        "expected_behavior": (
            "Retrieval finds useful local evidence, at least one local document graded relevant, "
            "workflow does not use web search, answer is grounded in evidence."
        ),
    },
    {
        "scenario_id": "Q2_STALE_VERSION_SPECIFIC",
        "query": "How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?",
        "expected_behavior": (
            "Evaluates frozen v1.31 KB; if local evidence is insufficient, activates corrective web search; "
            "final answer must only assert facts supported by available evidence or safely refuse."
        ),
    },
    {
        "scenario_id": "Q3_FICTIONAL_PREMISE",
        "query": "What does the --enable-quantum-scheduler flag do in kubectl?",
        "expected_behavior": (
            "Unsupported fictional premise; system must not invent behavior; "
            "terminal safe refusal is the expected outcome."
        ),
    },
]


def print_safety_message() -> None:
    """Prints safety explanation when run without --live flag."""
    print("============================================================")
    print("SAFETY NOTICE: Live Provider Evaluation")
    print("============================================================")
    print("This golden-scenario evaluation harness executes live calls")
    print("to external API providers (Groq LLM and Tavily Web Search).")
    print()
    print("To run the live evaluation harness, execute explicitly with:")
    print("    python scripts/evaluate_golden_scenarios.py --live")
    print("============================================================")


def print_scenario_console_report(result: ScenarioResult) -> None:
    """Prints learner-readable execution report for a scenario to console."""
    print("============================================================")
    print(f"{result.scenario_id}")
    print("============================================================")
    print("\nQuestion:")
    print(result.query)
    print("\nObserved route:")
    print(" -> ".join(result.observed_trace_steps) if result.observed_trace_steps else "None")
    print(f"\nWeb search used:\n{'Yes' if result.used_web_search else 'No'}")
    if result.rewritten_query:
        print(f"\nRewritten query:\n{result.rewritten_query}")
    print(f"\nGeneration attempts:\n{result.generation_attempts}")
    print(f"\nFinal status:\n{result.final_status}")
    print(f"\nFinal answer:\n{result.final_answer}")
    print(f"\nSources:\n{', '.join(result.final_sources) if result.final_sources else 'None'}")
    print(f"\nEvaluation:\n{result.evaluation_outcome}")
    if result.evaluation_notes:
        print(f"Notes: {'; '.join(result.evaluation_notes)}")
    print()


def main() -> None:
    """Main execution function for golden scenario evaluation harness."""
    parser = argparse.ArgumentParser(
        description="Run opt-in live golden scenario evaluation for Corrective RAG application."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Execute live evaluation calling Groq and Tavily APIs. Required to run harness.",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if not args.live:
        print_safety_message()
        sys.exit(0)

    print("Running Preflight Checks...")
    try:
        settings, model_name = run_preflight_checks()
    except Exception as exc:
        print(f"\n[PREFLIGHT ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Preflight Checks Passed. (Chroma path: '{settings.chroma_path}', Collection: '{settings.chroma_collection}', Model: '{model_name}')\n")

    print("Building application using production entrypoint 'build_application()'.")
    app = build_application(settings=settings)

    results: list[ScenarioResult] = []
    run_timestamp = datetime.now(timezone.utc)

    for scenario_info in GOLDEN_SCENARIOS:
        scenario_id = scenario_info["scenario_id"]
        query_text = scenario_info["query"]
        expected = scenario_info["expected_behavior"]

        print(f"Executing scenario: {scenario_id}...")
        started_at = datetime.now(timezone.utc)
        try:
            state = app.run(Question(text=query_text))
            completed_at = datetime.now(timezone.utc)
            res = extract_scenario_result(
                scenario_id=scenario_id,
                query=query_text,
                expected_behavior=expected,
                started_at=started_at,
                completed_at=completed_at,
                model_name=model_name,
                state=state,
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            elapsed_ms = (completed_at - started_at).total_seconds() * 1000.0
            res = ScenarioResult(
                scenario_id=scenario_id,
                query=query_text,
                started_at_utc=started_at.isoformat(),
                completed_at_utc=completed_at.isoformat(),
                elapsed_ms=elapsed_ms,
                model=model_name,
                final_status="ERROR",
                final_answer=f"Execution error: {exc}",
                generation_attempts=0,
                observed_trace_steps=[],
                used_web_search=False,
                rewritten_query=None,
                local_relevance=[],
                final_sources=[],
                supported=None,
                expected_behavior=expected,
                evaluation_outcome="ERROR",
                evaluation_notes=[f"Runtime failure: {exc}"],
            )

        print_scenario_console_report(res)
        results.append(res)

    pass_count = sum(1 for r in results if r.evaluation_outcome == "PASS")
    div_count = sum(1 for r in results if r.evaluation_outcome == "DIVERGENCE")
    err_count = sum(1 for r in results if r.evaluation_outcome == "ERROR")

    summary = {
        "total_scenarios": len(results),
        "pass_count": pass_count,
        "divergence_count": div_count,
        "error_count": err_count,
    }

    metadata = {
        "evaluation_type": "golden_scenario_live",
        "timestamp_utc": run_timestamp.isoformat(),
        "model": model_name,
        "kb_snapshot": "Kubernetes website v1.31 (snapshot-initial-v1.31 / commit 20d164c)",
        "chroma_collection": settings.chroma_collection,
        "retriever_top_k": settings.retriever_top_k,
        "generation_max_attempts": 2,
        "notice": "This is an observational live evaluation using nondeterministic external models/providers.",
    }

    report = GoldenEvaluationReport(
        metadata=metadata,
        scenario_results=results,
        summary=summary,
    )

    artifacts_dir = Path("artifacts/evaluations")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    filename = f"crag-golden-evaluation-{run_timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    artifact_path = artifacts_dir / filename

    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)

    print("============================================================")
    print("SUMMARY")
    print("============================================================")
    for r in results:
        dots = "." * max(2, 35 - len(r.scenario_id))
        print(f"{r.scenario_id} {dots} {r.evaluation_outcome}")
    print()
    print(f"Artifact:\n{artifact_path.as_posix()}")
    print("============================================================")


if __name__ == "__main__":
    main()
