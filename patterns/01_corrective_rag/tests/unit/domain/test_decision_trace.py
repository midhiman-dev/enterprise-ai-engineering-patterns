"""Unit tests for DecisionTrace domain entity."""

from datetime import datetime
import pytest

from corrective_rag.domain.entities import DecisionTrace, TraceStep


def test_trace_step_validation() -> None:
    """Verifies TraceStep construction and invariant checks."""
    step = TraceStep(name="retrieve", detail="Retrieved 4 local documents")

    assert step.name == "retrieve"
    assert step.detail == "Retrieved 4 local documents"
    assert isinstance(step.timestamp, datetime)

    with pytest.raises(ValueError, match="TraceStep name cannot be empty"):
        TraceStep(name="")


def test_decision_trace_starts_empty() -> None:
    """Verifies that a new DecisionTrace contains zero steps."""
    trace = DecisionTrace()

    assert len(trace) == 0
    assert len(trace.steps) == 0


def test_decision_trace_records_and_preserves_step_order() -> None:
    """Verifies that steps are recorded in explicit execution order."""
    trace = DecisionTrace()

    s1 = trace.add_step("retrieve", "Queried vector store with original question")
    s2 = trace.add_step("grade_documents", "0 of 4 documents relevant")
    s3 = trace.add_step("rewrite_query", "Transformed query for web search")
    s4 = trace.add_step("web_search", "Retrieved 3 web documents from Tavily")
    s5 = trace.add_step("generate", "Generated answer using web evidence")

    assert len(trace) == 5
    assert trace.steps[0].name == "retrieve"
    assert trace.steps[1].name == "grade_documents"
    assert trace.steps[2].name == "rewrite_query"
    assert trace.steps[3].name == "web_search"
    assert trace.steps[4].name == "generate"

    assert trace.steps[0] == s1
    assert trace.steps[4] == s5


def test_decision_trace_returns_immutable_sequence() -> None:
    """Verifies that trace.steps property returns an immutable view."""
    trace = DecisionTrace()
    trace.add_step("retrieve")

    steps_view = trace.steps
    assert isinstance(steps_view, tuple)
