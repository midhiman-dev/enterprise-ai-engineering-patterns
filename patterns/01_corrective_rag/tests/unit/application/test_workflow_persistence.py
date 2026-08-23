"""Application unit tests verifying DecisionTrace persistence across terminal workflow paths via CorrectiveRAGApplication."""

import pytest

from corrective_rag.application.application import CorrectiveRAGApplication
from corrective_rag.application.workflow import build_graph
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from tests.unit.application.fakes import (
    FakeDecisionTraceRepository,
    FakeGenerator,
    FakeHallucinationChecker,
    FakeQueryRewriter,
    FakeRelevanceGrader,
    FakeRetriever,
    FakeWebSearchProvider,
)


def test_golden_query_1_straight_path_persists_trace() -> None:
    """Golden Query 1: Straight-through workflow execution via Application runtime persists DecisionTrace once."""
    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    doc = Document(content="CrashLoopBackOff indicates container failure.", source="k8s.md")
    expected_answer = Answer(text="Container failure occurred.", status=AnswerStatus.ANSWERED)
    fake_repo = FakeDecisionTraceRepository()

    deps = WorkflowDependencies(
        retriever=FakeRetriever(documents=[doc]),
        relevance_grader=FakeRelevanceGrader(default_is_relevant=True),
        query_rewriter=FakeQueryRewriter(),
        generator=FakeGenerator(answer=expected_answer),
        web_search_provider=FakeWebSearchProvider(),
        hallucination_checker=FakeHallucinationChecker(is_supported=True),
    )

    app = CorrectiveRAGApplication(
        graph=build_graph(deps),
        repository=fake_repo,
    )

    result = app.run(question=question)

    assert result["answer"] == expected_answer
    assert len(fake_repo.saved_traces) == 1
    persisted_trace = fake_repo.saved_traces[0]
    assert [step.name for step in persisted_trace.steps] == [
        "retrieve",
        "grade_documents",
        "generate",
        "hallucination_check",
    ]


def test_golden_query_2_corrective_path_persists_trace() -> None:
    """Golden Query 2: Corrective search workflow execution via Application runtime persists DecisionTrace once."""
    question = Question(text="What is the latest Kubernetes release?")
    web_doc = Document(content="Kubernetes 1.30 was released recently.", source="web_search")
    fake_repo = FakeDecisionTraceRepository()

    deps = WorkflowDependencies(
        retriever=FakeRetriever(documents=[]),  # No local docs
        relevance_grader=FakeRelevanceGrader(default_is_relevant=False),
        query_rewriter=FakeQueryRewriter(),
        generator=FakeGenerator(
            answer=Answer(text="Kubernetes 1.30 released.", status=AnswerStatus.ANSWERED)
        ),
        web_search_provider=FakeWebSearchProvider(documents=[web_doc]),
        hallucination_checker=FakeHallucinationChecker(is_supported=True),
    )

    app = CorrectiveRAGApplication(
        graph=build_graph(deps),
        repository=fake_repo,
    )

    result = app.run(question=question)

    assert result["answer"].status == AnswerStatus.ANSWERED
    assert len(fake_repo.saved_traces) == 1
    persisted_trace = fake_repo.saved_traces[0]
    assert [step.name for step in persisted_trace.steps] == [
        "retrieve",
        "grade_documents",
        "rewrite_query",
        "web_search",
        "generate",
        "hallucination_check",
    ]


def test_golden_query_3_safe_refusal_persists_trace() -> None:
    """Golden Query 3: Grounding failure leading to safe refusal via Application runtime persists complete trace."""
    question = Question(text="Fabricated claim question")
    fake_repo = FakeDecisionTraceRepository()

    deps = WorkflowDependencies(
        retriever=FakeRetriever(documents=[]),
        relevance_grader=FakeRelevanceGrader(default_is_relevant=False),
        query_rewriter=FakeQueryRewriter(),
        generator=FakeGenerator(
            answers=[
                Answer(text="Unverified claim 1", status=AnswerStatus.ANSWERED),
                Answer(text="Unverified claim 2", status=AnswerStatus.ANSWERED),
            ]
        ),
        web_search_provider=FakeWebSearchProvider(
            documents=[Document(content="Search result", source="web")]
        ),
        hallucination_checker=FakeHallucinationChecker(is_supported=False),
    )

    app = CorrectiveRAGApplication(
        graph=build_graph(deps),
        repository=fake_repo,
    )

    result = app.run(question=question)

    assert result["answer"].status == AnswerStatus.UNSUPPORTED
    assert len(fake_repo.saved_traces) == 1
    persisted_trace = fake_repo.saved_traces[0]
    assert [step.name for step in persisted_trace.steps] == [
        "retrieve",
        "grade_documents",
        "rewrite_query",
        "web_search",
        "generate",
        "hallucination_check",
        "generate",
        "hallucination_check",
        "safe_refusal",
    ]


class BrokenTraceRepository:
    """Failing repository for testing operational exception propagation."""

    def save(self, trace: object) -> None:
        raise RuntimeError("Database connection failure during save.")


def test_persistence_failure_raises_operational_exception() -> None:
    """Verifies that persistence failure raises operational exception and is not swallowed."""
    question = Question(text="Simple test question")
    doc = Document(content="Valid content", source="k8s.md")
    broken_repo = BrokenTraceRepository()

    deps = WorkflowDependencies(
        retriever=FakeRetriever(documents=[doc]),
        relevance_grader=FakeRelevanceGrader(default_is_relevant=True),
        query_rewriter=FakeQueryRewriter(),
        generator=FakeGenerator(answer=Answer(text="Valid answer", status=AnswerStatus.ANSWERED)),
        web_search_provider=FakeWebSearchProvider(),
        hallucination_checker=FakeHallucinationChecker(is_supported=True),
    )

    app = CorrectiveRAGApplication(
        graph=build_graph(deps),
        repository=broken_repo,  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="Database connection failure during save"):
        app.run(question=question)
