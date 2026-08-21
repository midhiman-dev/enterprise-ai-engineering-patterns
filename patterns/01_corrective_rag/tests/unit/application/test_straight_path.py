"""Unit tests for the Pass-3 LangGraph straight-path execution workflow."""

from corrective_rag.application.workflow import build_graph, create_initial_state
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from tests.unit.application.fakes import (
    FakeGenerator,
    FakeHallucinationChecker,
    FakeRelevanceGrader,
    FakeRetriever,
)


def test_straight_path_execution_golden_query() -> None:
    """Core Pass-3 Acceptance Test: Verifies straight-through workflow execution.

    Golden Query: Why does kubectl get pods show CrashLoopBackOff?
    Path: START -> retrieve -> grade_documents -> generate -> hallucination_check -> END
    """
    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    doc1 = Document(
        content="CrashLoopBackOff indicates a container failed to start or repeatedly crashes after starting.",
        source="k8s_docs/troubleshooting.md",
    )
    doc2 = Document(
        content="Check pod logs using kubectl logs <pod-name> to inspect application exit codes.",
        source="k8s_docs/logging.md",
    )
    expected_answer = Answer(
        text="CrashLoopBackOff occurs when a container repeatedly exits unexpectedly. Inspect pod logs to diagnose.",
        status=AnswerStatus.ANSWERED,
    )

    retriever = FakeRetriever(documents=[doc1, doc2])
    grader = FakeRelevanceGrader(default_is_relevant=True)
    generator = FakeGenerator(answer=expected_answer)
    checker = FakeHallucinationChecker(is_supported=True)

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        generator=generator,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    initial_state = create_initial_state(question)
    result = graph.invoke(initial_state)

    # 1. State assertions
    assert result["question"] == question
    assert result["documents"] == [doc1, doc2]
    assert len(result["graded_documents"]) == 2
    assert result["answer"] == expected_answer
    assert result["is_supported"] is True

    # 2. DecisionTrace step order assertion
    trace_step_names = [step.name for step in result["trace"].steps]
    assert trace_step_names == [
        "retrieve",
        "grade_documents",
        "generate",
        "hallucination_check",
    ]


def test_grading_filters_irrelevant_documents() -> None:
    """Verifies that relevance grading filters out irrelevant documents before generation."""
    question = Question(text="Why does kubectl get pods show CrashLoopBackOff?")
    doc_rel_1 = Document(content="Relevant Kubernetes log info", source="doc_rel_1")
    doc_rel_2 = Document(content="Relevant Kubernetes exit code info", source="doc_rel_2")
    doc_irrel = Document(content="Unrelated database backup guide", source="doc_irrel")

    retriever = FakeRetriever(documents=[doc_rel_1, doc_irrel, doc_rel_2])
    grader = FakeRelevanceGrader(
        relevant_document_sources=["doc_rel_1", "doc_rel_2"],
    )
    expected_answer = Answer(text="Grounded answer from relevant docs", status=AnswerStatus.ANSWERED)
    generator = FakeGenerator(answer=expected_answer)
    checker = FakeHallucinationChecker(is_supported=True)

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        generator=generator,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    result = graph.invoke(create_initial_state(question))

    # All candidate documents evaluated by grader
    assert len(result["graded_documents"]) == 3
    # Only relevant documents passed forward in state
    assert result["documents"] == [doc_rel_1, doc_rel_2]

    # Generator received ONLY the 2 relevant documents
    assert len(generator.received_calls) == 1
    gen_question, gen_docs = generator.received_calls[0]
    assert gen_question == question
    assert gen_docs == (doc_rel_1, doc_rel_2)


def test_dependency_call_sequence_and_arguments() -> None:
    """Verifies that each domain port receives exact expected inputs in execution order."""
    question = Question(text="How do I inspect pod descriptions?")
    doc = Document(content="Use kubectl describe pod <pod-name>", source="k8s_docs/describe.md")
    expected_answer = Answer(text="Use kubectl describe pod.", status=AnswerStatus.ANSWERED)

    retriever = FakeRetriever(documents=[doc])
    grader = FakeRelevanceGrader(default_is_relevant=True)
    generator = FakeGenerator(answer=expected_answer)
    checker = FakeHallucinationChecker(is_supported=True)

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        generator=generator,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    graph.invoke(create_initial_state(question))

    # Retriever received question
    assert retriever.received_questions == [question]

    # Grader received question + document
    assert grader.received_grades == [(question, doc)]

    # Generator received question + relevant documents tuple
    assert generator.received_calls == [(question, (doc,))]

    # HallucinationChecker received candidate answer + relevant documents tuple
    assert checker.received_checks == [(expected_answer, (doc,))]
