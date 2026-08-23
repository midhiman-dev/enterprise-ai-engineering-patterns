"""Unit tests for CorrectiveRAGApplication runtime boundary."""

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


def test_corrective_rag_application_run_executes_and_persists() -> None:
    """Verifies CorrectiveRAGApplication bundles state graph and repository and executes workflow."""
    question = Question(text="What is Clean Architecture?")
    doc = Document(content="Clean Architecture decouples core logic from I/O.", source="doc.md")
    expected_answer = Answer(text="Architecture design pattern.", status=AnswerStatus.ANSWERED)
    fake_repo = FakeDecisionTraceRepository()

    deps = WorkflowDependencies(
        retriever=FakeRetriever(documents=[doc]),
        relevance_grader=FakeRelevanceGrader(default_is_relevant=True),
        query_rewriter=FakeQueryRewriter(),
        generator=FakeGenerator(answer=expected_answer),
        web_search_provider=FakeWebSearchProvider(),
        hallucination_checker=FakeHallucinationChecker(is_supported=True),
        decision_trace_repository=fake_repo,
    )

    graph = build_graph(deps)
    app = CorrectiveRAGApplication(graph=graph, repository=fake_repo)

    assert app.graph is graph
    assert app.repository is fake_repo

    result = app.run(question)

    assert result["answer"] == expected_answer
    assert len(fake_repo.saved_traces) == 1
