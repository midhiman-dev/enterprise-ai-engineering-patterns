"""Unit tests for offline evaluation harness logic and classification rules."""

from datetime import datetime, timezone
import json
from unittest.mock import MagicMock, patch

import pytest

from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.graded_document import GradedDocument
from corrective_rag.domain.entities.question import Question
from corrective_rag.evaluation.evaluation_models import (
    GoldenEvaluationReport,
    LocalRelevanceRecord,
    ScenarioResult,
)
from corrective_rag.evaluation.evaluator import (
    EXACT_SAFE_REFUSAL_TEXT,
    classify_scenario_result,
    extract_scenario_result,
    run_preflight_checks,
)
from scripts.evaluate_golden_scenarios import main as evaluate_main


def test_evaluate_golden_scenarios_without_live_flag_exits_cleanly(capsys):
    """Confirm running evaluate_golden_scenarios.py without --live does not call live APIs and exits cleanly."""
    with patch("sys.argv", ["evaluate_golden_scenarios.py"]):
        with pytest.raises(SystemExit) as exc_info:
            evaluate_main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "SAFETY NOTICE" in captured.out
    assert "--live" in captured.out


def test_preflight_checks_missing_or_empty_chroma_collection():
    """Confirm preflight checks fail clearly if Chroma collection is missing or empty."""
    with patch("corrective_rag.evaluation.evaluator.load_local_environment"), \
         patch("corrective_rag.evaluation.evaluator.load_groq_config_from_env") as mock_groq, \
         patch("corrective_rag.evaluation.evaluator.load_tavily_config_from_env"), \
         patch("corrective_rag.evaluation.evaluator.load_application_settings_from_env") as mock_settings, \
         patch("chromadb.PersistentClient") as mock_chroma_client:

        mock_groq.return_value.model = "test-model"
        mock_settings.return_value.chroma_path = "data/chroma"
        mock_settings.return_value.chroma_collection = "corrective-rag-kb"

        # Case A: Collection missing / raises Exception
        mock_client_inst = MagicMock()
        mock_client_inst.get_collection.side_effect = Exception("Collection not found")
        mock_chroma_client.return_value = mock_client_inst

        with pytest.raises(RuntimeError, match="Build the frozen KB index before running the live evaluation"):
            run_preflight_checks()

        # Case B: Collection exists but count == 0
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_client_inst.get_collection.side_effect = None
        mock_client_inst.get_collection.return_value = mock_collection

        with pytest.raises(RuntimeError, match="is empty \\(0 indexed chunks\\)"):
            run_preflight_checks()


def test_result_serialization_produces_deterministic_json():
    """Confirm ScenarioResult and GoldenEvaluationReport produce expected JSON dictionary structure."""
    record = LocalRelevanceRecord(
        source="doc1.md",
        title="Title 1",
        relevance_result=True,
        score=0.95,
        reason="Matches query",
    )
    result = ScenarioResult(
        scenario_id="Q1_LOCAL_KNOWN",
        query="Test query",
        started_at_utc="2026-08-31T12:00:00Z",
        completed_at_utc="2026-08-31T12:00:01Z",
        elapsed_ms=1000.0,
        model="test-model",
        final_status="ANSWERED",
        final_answer="Test answer",
        generation_attempts=1,
        observed_trace_steps=["retrieve", "grade_documents", "generate", "hallucination_check"],
        used_web_search=False,
        rewritten_query=None,
        local_relevance=[record],
        final_sources=["doc1.md"],
        supported=True,
        expected_behavior="Expected behavior text",
        evaluation_outcome="PASS",
        evaluation_notes=["Note 1"],
    )

    report = GoldenEvaluationReport(
        metadata={"test": "meta"},
        scenario_results=[result],
        summary={"total_scenarios": 1, "pass_count": 1, "divergence_count": 0, "error_count": 0},
    )

    d = report.to_dict()
    json_str = json.dumps(d)
    parsed = json.loads(json_str)

    assert parsed["metadata"]["test"] == "meta"
    assert parsed["scenario_results"][0]["scenario_id"] == "Q1_LOCAL_KNOWN"
    assert parsed["scenario_results"][0]["used_web_search"] is False
    assert parsed["summary"]["pass_count"] == 1


def test_used_web_search_derived_from_observed_trace():
    """Confirm used_web_search is derived strictly from presence of 'web_search' in trace steps."""
    now = datetime.now(timezone.utc)
    trace = DecisionTrace()
    trace.add_step("retrieve")
    trace.add_step("grade_documents")
    trace.add_step("rewrite_query")
    trace.add_step("web_search")
    trace.add_step("generate")

    doc = Document(content="web doc content", source="https://example.com/web")
    state = {
        "question": Question(text="stale query"),
        "rewritten_question": Question(text="rewritten query"),
        "documents": [doc],
        "graded_documents": [],
        "answer": Answer(text="web answer", status=AnswerStatus.ANSWERED),
        "is_supported": True,
        "generation_attempts": 1,
        "trace": trace,
    }

    res = extract_scenario_result(
        scenario_id="Q2_STALE_VERSION_SPECIFIC",
        query="stale query",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state,
    )

    assert res.used_web_search is True
    assert res.observed_trace_steps == ["retrieve", "grade_documents", "rewrite_query", "web_search", "generate"]
    assert res.rewritten_query == "rewritten query"


def test_q1_evaluation_classification_pass_and_divergence():
    """Confirm Q1 classification rules: local answer -> PASS, web-search route -> DIVERGENCE."""
    now = datetime.now(timezone.utc)

    # Q1 PASS case
    trace_pass = DecisionTrace()
    trace_pass.add_step("retrieve")
    trace_pass.add_step("grade_documents")
    trace_pass.add_step("generate")
    trace_pass.add_step("hallucination_check")

    doc = Document(content="pod crash detail", source="k8s_doc.md")
    gdoc = GradedDocument(document=doc, is_relevant=True)
    state_pass = {
        "question": Question(text="CrashLoopBackOff"),
        "rewritten_question": None,
        "documents": [doc],
        "graded_documents": [gdoc],
        "answer": Answer(text="CrashLoopBackOff happens when...", status=AnswerStatus.ANSWERED),
        "is_supported": True,
        "generation_attempts": 1,
        "trace": trace_pass,
    }

    res_pass = extract_scenario_result(
        scenario_id="Q1_LOCAL_KNOWN",
        query="Why CrashLoopBackOff?",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state_pass,
    )
    assert res_pass.evaluation_outcome == "PASS"

    # Q1 DIVERGENCE case (web search used)
    trace_div = DecisionTrace()
    trace_div.add_step("retrieve")
    trace_div.add_step("grade_documents")
    trace_div.add_step("rewrite_query")
    trace_div.add_step("web_search")
    trace_div.add_step("generate")

    state_div = {
        "question": Question(text="CrashLoopBackOff"),
        "rewritten_question": Question(text="CrashLoopBackOff k8s"),
        "documents": [doc],
        "graded_documents": [],
        "answer": Answer(text="Answer from web", status=AnswerStatus.ANSWERED),
        "is_supported": True,
        "generation_attempts": 1,
        "trace": trace_div,
    }

    res_div = extract_scenario_result(
        scenario_id="Q1_LOCAL_KNOWN",
        query="Why CrashLoopBackOff?",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state_div,
    )
    assert res_div.evaluation_outcome == "DIVERGENCE"


def test_q2_evaluation_classification_pass_scenarios():
    """Confirm Q2 classification rules: corrective route + grounded answer or safe refusal -> PASS."""
    now = datetime.now(timezone.utc)
    trace = DecisionTrace()
    trace.add_step("retrieve")
    trace.add_step("grade_documents")
    trace.add_step("rewrite_query")
    trace.add_step("web_search")
    trace.add_step("generate")

    # Q2 PASS case A: corrective route + grounded answer
    doc = Document(content="v1.32 eviction info", source="https://k8s.io/docs")
    state_a = {
        "question": Question(text="v1.32 eviction"),
        "rewritten_question": Question(text="v1.32 eviction policy"),
        "documents": [doc],
        "graded_documents": [],
        "answer": Answer(text="Under k8s 1.32...", status=AnswerStatus.ANSWERED),
        "is_supported": True,
        "generation_attempts": 1,
        "trace": trace,
    }

    res_a = extract_scenario_result(
        scenario_id="Q2_STALE_VERSION_SPECIFIC",
        query="v1.32 eviction",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state_a,
    )
    assert res_a.evaluation_outcome == "PASS"

    # Q2 PASS case B: corrective route + safe refusal
    state_b = {
        "question": Question(text="v1.32 eviction"),
        "rewritten_question": Question(text="v1.32 eviction policy"),
        "documents": [],
        "graded_documents": [],
        "answer": Answer(text=EXACT_SAFE_REFUSAL_TEXT, status=AnswerStatus.UNSUPPORTED),
        "is_supported": False,
        "generation_attempts": 2,
        "trace": trace,
    }

    res_b = extract_scenario_result(
        scenario_id="Q2_STALE_VERSION_SPECIFIC",
        query="v1.32 eviction",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state_b,
    )
    assert res_b.evaluation_outcome == "PASS"


def test_q3_evaluation_classification_pass_and_divergence():
    """Confirm Q3 classification rules: exact safe refusal -> PASS, ANSWERED -> DIVERGENCE."""
    now = datetime.now(timezone.utc)
    trace = DecisionTrace()
    trace.add_step("retrieve")
    trace.add_step("grade_documents")
    trace.add_step("generate")
    trace.add_step("hallucination_check")
    trace.add_step("safe_refusal")

    # Q3 PASS case: exact safe refusal
    state_pass = {
        "question": Question(text="--enable-quantum-scheduler"),
        "rewritten_question": None,
        "documents": [],
        "graded_documents": [],
        "answer": Answer(text=EXACT_SAFE_REFUSAL_TEXT, status=AnswerStatus.UNSUPPORTED),
        "is_supported": False,
        "generation_attempts": 2,
        "trace": trace,
    }

    res_pass = extract_scenario_result(
        scenario_id="Q3_FICTIONAL_PREMISE",
        query="quantum flag",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state_pass,
    )
    assert res_pass.evaluation_outcome == "PASS"

    # Q3 DIVERGENCE case: answered
    doc = Document(content="fictional info", source="fake.md")
    state_div = {
        "question": Question(text="--enable-quantum-scheduler"),
        "rewritten_question": None,
        "documents": [doc],
        "graded_documents": [],
        "answer": Answer(text="The quantum scheduler enables quantum computing...", status=AnswerStatus.ANSWERED),
        "is_supported": True,
        "generation_attempts": 1,
        "trace": trace,
    }

    res_div = extract_scenario_result(
        scenario_id="Q3_FICTIONAL_PREMISE",
        query="quantum flag",
        expected_behavior="exp",
        started_at=now,
        completed_at=now,
        model_name="test-model",
        state=state_div,
    )
    assert res_div.evaluation_outcome == "DIVERGENCE"


def test_error_scenario_records_failure_without_fabrication():
    """Confirm runtime error records ERROR outcome without fabricating successful result."""
    result = ScenarioResult(
        scenario_id="Q1_LOCAL_KNOWN",
        query="query",
        started_at_utc="2026-08-31T12:00:00Z",
        completed_at_utc="2026-08-31T12:00:01Z",
        elapsed_ms=100.0,
        model="test-model",
        final_status="ERROR",
        final_answer="Execution error: Groq API timeout",
        generation_attempts=0,
        observed_trace_steps=[],
        used_web_search=False,
        rewritten_query=None,
        local_relevance=[],
        final_sources=[],
        supported=None,
        expected_behavior="exp",
        evaluation_outcome="ERROR",
        evaluation_notes=["Runtime failure: Groq API timeout"],
    )

    classified = classify_scenario_result(result)
    assert classified.evaluation_outcome == "ERROR"
    assert "Runtime failure" in classified.evaluation_notes[0]
