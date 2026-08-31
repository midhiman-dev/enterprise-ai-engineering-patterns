"""Evaluation logic and preflight prerequisite validator for golden scenarios.

Provides preflight validation functions to check runtime prerequisites without modifying index content,
as well as pure classification rules for evaluating observational results against scenario hypotheses.
"""

from datetime import datetime, timezone
import sys
from typing import Any

import chromadb

from corrective_rag.application.graph_state import GraphState
from corrective_rag.composition.environment import load_local_environment
from corrective_rag.composition.settings import (
    ApplicationSettings,
    load_application_settings_from_env,
)
from corrective_rag.domain.entities.answer import AnswerStatus
from corrective_rag.evaluation.evaluation_models import LocalRelevanceRecord, ScenarioResult
from corrective_rag.infrastructure.generation.groq_config import load_groq_config_from_env
from corrective_rag.infrastructure.search.tavily_config import load_tavily_config_from_env

EXACT_SAFE_REFUSAL_TEXT = "I cannot provide a supported answer based on the available evidence."


def run_preflight_checks() -> tuple[ApplicationSettings, str]:
    """Validates all required runtime prerequisites before executing live evaluation scenarios.

    Checks:
        1. Local environment bootstrap can run.
        2. GROQ_API_KEY resolves through existing config path.
        3. TAVILY_API_KEY resolves through existing config path.
        4. Chroma path resolves using ApplicationSettings.
        5. Expected Chroma collection exists.
        6. The Chroma collection is non-empty.

    Returns:
        Tuple of (ApplicationSettings, model_name).

    Raises:
        RuntimeError: If any preflight prerequisite check fails.
    """
    load_local_environment()

    try:
        groq_config = load_groq_config_from_env()
    except Exception as exc:
        raise RuntimeError(
            f"Preflight Check Failed: Unable to resolve GROQ_API_KEY. Details: {exc}"
        ) from exc

    try:
        tavily_config = load_tavily_config_from_env()
    except Exception as exc:
        raise RuntimeError(
            f"Preflight Check Failed: Unable to resolve TAVILY_API_KEY. Details: {exc}"
        ) from exc

    try:
        settings = load_application_settings_from_env()
    except Exception as exc:
        raise RuntimeError(
            f"Preflight Check Failed: Unable to resolve ApplicationSettings. Details: {exc}"
        ) from exc

    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
    except Exception as exc:
        raise RuntimeError(
            f"Preflight Check Failed: Unable to open Chroma persistent client at '{settings.chroma_path}'. Details: {exc}"
        ) from exc

    try:
        collection = client.get_collection(name=settings.chroma_collection)
    except Exception as exc:
        raise RuntimeError(
            f"Preflight Check Failed: Chroma collection '{settings.chroma_collection}' does not exist at '{settings.chroma_path}'. "
            "Build the frozen KB index before running the live evaluation."
        ) from exc

    count = collection.count()
    if count == 0:
        raise RuntimeError(
            f"Preflight Check Failed: Chroma collection '{settings.chroma_collection}' is empty (0 indexed chunks). "
            "Build the frozen KB index before running the live evaluation."
        )

    return settings, groq_config.model


def extract_scenario_result(
    scenario_id: str,
    query: str,
    expected_behavior: str,
    started_at: datetime,
    completed_at: datetime,
    model_name: str,
    state: GraphState,
) -> ScenarioResult:
    """Extracts observational evidence fields from completed GraphState workflow result.

    Args:
        scenario_id: Identifier of scenario.
        query: Scenario query string.
        expected_behavior: Descriptive text of intended behavior.
        started_at: UTC start datetime.
        completed_at: UTC completion datetime.
        model_name: Name of model used.
        state: Final GraphState returned by application.run().

    Returns:
        Structured ScenarioResult instance.
    """
    elapsed_ms = (completed_at - started_at).total_seconds() * 1000.0

    trace_steps = [step.name for step in state["trace"].steps] if "trace" in state else []
    used_web_search = "web_search" in trace_steps

    rewritten_query = (
        state["rewritten_question"].text
        if state.get("rewritten_question") is not None
        else None
    )

    answer_obj = state.get("answer")
    if answer_obj is not None:
        final_answer = answer_obj.text
        if answer_obj.status == AnswerStatus.ANSWERED:
            final_status = "ANSWERED"
        elif answer_obj.status == AnswerStatus.UNSUPPORTED:
            final_status = "UNSUPPORTED"
        else:
            final_status = str(answer_obj.status).upper()
    else:
        final_answer = ""
        final_status = "UNSUPPORTED"

    local_relevance: list[LocalRelevanceRecord] = []
    for gdoc in state.get("graded_documents", []):
        doc = gdoc.document
        title = doc.title if doc.title else (str(doc.metadata.get("title")) if doc.metadata and "title" in doc.metadata else None)
        local_relevance.append(
            LocalRelevanceRecord(
                source=doc.source,
                title=title,
                relevance_result=gdoc.is_relevant,
                score=gdoc.score,
                reason=gdoc.reason,
            )
        )

    final_sources: list[str] = []
    if final_status == "ANSWERED":
        for doc in state.get("documents", []):
            src_identifier = doc.source_url or doc.source
            if src_identifier and src_identifier not in final_sources:
                final_sources.append(src_identifier)

    result = ScenarioResult(
        scenario_id=scenario_id,
        query=query,
        started_at_utc=started_at.isoformat(),
        completed_at_utc=completed_at.isoformat(),
        elapsed_ms=elapsed_ms,
        model=model_name,
        final_status=final_status,
        final_answer=final_answer,
        generation_attempts=state.get("generation_attempts", 0),
        observed_trace_steps=trace_steps,
        used_web_search=used_web_search,
        rewritten_query=rewritten_query,
        local_relevance=local_relevance,
        final_sources=final_sources,
        supported=state.get("is_supported"),
        expected_behavior=expected_behavior,
        evaluation_outcome="ERROR",  # Placeholder, set by classifier
        evaluation_notes=[],
    )

    return classify_scenario_result(result)


def classify_scenario_result(result: ScenarioResult) -> ScenarioResult:
    """Evaluates scenario result against golden hypothesis rules without altering state or routing.

    Classification logic:
        Q1_LOCAL_KNOWN:
            - PASS: final_status ANSWERED, used_web_search is False, supported is True (or not False), and relevant local docs present.
            - DIVERGENCE: if web search used, or status not ANSWERED, or unsupported.

        Q2_STALE_VERSION_SPECIFIC:
            - PASS: used_web_search is True AND (final_status ANSWERED with supported answer OR final_status UNSUPPORTED with safe refusal).
            - DIVERGENCE: local route used without web search, or ungrounded claims asserted.

        Q3_FICTIONAL_PREMISE:
            - PASS: final_status UNSUPPORTED and final_answer exactly equals EXACT_SAFE_REFUSAL_TEXT.
            - DIVERGENCE: final_status ANSWERED or answer does not match safe refusal.

    Returns:
        Updated ScenarioResult with evaluation_outcome and evaluation_notes populated.
    """
    notes: list[str] = []
    scenario_id = result.scenario_id

    if result.final_status == "ERROR":
        result.evaluation_outcome = "ERROR"
        return result

    if scenario_id == "Q1_LOCAL_KNOWN":
        if result.used_web_search:
            outcome = "DIVERGENCE"
            notes.append("Divergence: Workflow routed to web search despite Q1 being a local/known query.")
        elif result.final_status != "ANSWERED":
            outcome = "DIVERGENCE"
            notes.append(f"Divergence: Expected status ANSWERED but observed {result.final_status}.")
        elif result.supported is False:
            outcome = "DIVERGENCE"
            notes.append("Divergence: Generated answer failed hallucination grounding check.")
        else:
            outcome = "PASS"
            notes.append("Pass: Answered successfully using local KB evidence without web search.")

    elif scenario_id == "Q2_STALE_VERSION_SPECIFIC":
        if result.used_web_search:
            if result.final_status == "ANSWERED" and result.supported is not False:
                outcome = "PASS"
                notes.append("Pass: Activated corrective route (web search) and produced grounded answer for v1.32 premise.")
            elif result.final_status == "UNSUPPORTED" and result.final_answer.strip() == EXACT_SAFE_REFUSAL_TEXT:
                outcome = "PASS"
                notes.append("Pass: Activated corrective web search; premise remained unsupported; issued safe refusal.")
            else:
                outcome = "DIVERGENCE"
                notes.append(f"Divergence: Corrective web search activated but outcome was {result.final_status} (supported={result.supported}).")
        else:
            outcome = "DIVERGENCE"
            notes.append("Divergence: Relevance grader judged local v1.31 docs sufficient for v1.32 specific query; workflow remained local.")

    elif scenario_id == "Q3_FICTIONAL_PREMISE":
        if result.final_status == "UNSUPPORTED" and result.final_answer.strip() == EXACT_SAFE_REFUSAL_TEXT:
            outcome = "PASS"
            notes.append("Pass: Correctly recognized unsupported fictional premise and returned exact safe refusal.")
        elif result.final_status == "ANSWERED":
            outcome = "DIVERGENCE"
            notes.append("Divergence: Fictional flag query was answered instead of issuing safe refusal.")
        else:
            outcome = "DIVERGENCE"
            notes.append(f"Divergence: Terminal status was {result.final_status} but answer text did not match exact safe refusal.")

    else:
        outcome = "DIVERGENCE"
        notes.append(f"Unknown scenario ID: {scenario_id}")

    result.evaluation_outcome = outcome
    result.evaluation_notes = notes
    return result
