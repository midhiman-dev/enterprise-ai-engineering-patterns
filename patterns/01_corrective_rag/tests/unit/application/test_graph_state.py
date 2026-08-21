"""Unit tests for GraphState and initial state creation helper."""

from corrective_rag.application.workflow import create_initial_state
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.question import Question


def test_create_initial_state_defaults() -> None:
    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    state = create_initial_state(question)

    assert state["question"] == question
    assert state["rewritten_question"] is None
    assert state["documents"] == []
    assert state["graded_documents"] == []
    assert state["answer"] is None
    assert state["is_supported"] is None
    assert state["generation_attempts"] == 0
    assert isinstance(state["trace"], DecisionTrace)
    assert len(state["trace"]) == 0


def test_create_initial_state_preserves_provided_trace() -> None:
    question = Question(text="What is a Kubernetes Pod?")
    trace = DecisionTrace()
    trace.add_step("initialization", "Started workflow")

    state = create_initial_state(question, trace=trace)

    assert state["trace"] is trace
    assert len(state["trace"]) == 1
    assert state["trace"].steps[0].name == "initialization"
