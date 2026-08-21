"""Unit tests for Pass-5 bounded hallucination retry and safe refusal execution path."""

from corrective_rag.application.workflow import MAX_GENERATION_ATTEMPTS, build_graph, create_initial_state
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from tests.unit.application.fakes import (
    FakeGenerator,
    FakeHallucinationChecker,
    FakeQueryRewriter,
    FakeRelevanceGrader,
    FakeRetriever,
    FakeWebSearchProvider,
)


def test_golden_query_3_fabricated_premise_safe_refusal() -> None:
    """Core Pass-5 Acceptance Test: Verifies safe refusal on fabricated premise.

    Golden Query 3: What does the --enable-quantum-scheduler flag do in kubectl?
    Path: retrieve -> grade_documents -> rewrite_query -> web_search -> generate -> hallucination_check -> generate -> hallucination_check -> safe_refusal -> END
    """
    question = Question(text="What does the --enable-quantum-scheduler flag do in kubectl?")
    irrelevant_local_doc = Document(content="kubectl scheduler flags reference", source="local/flags.md")
    rewritten_query = Question(text="kubectl --enable-quantum-scheduler flag description")
    web_doc = Document(content="Official kubectl command line flags documentation", source="https://kubernetes.io/docs")

    candidate_1 = Answer(
        text="The --enable-quantum-scheduler flag enables experimental quantum pod scheduling algorithms.",
        status=AnswerStatus.ANSWERED,
    )
    candidate_2 = Answer(
        text="This flag configures quantum queue optimizations in the Kubernetes scheduler controller.",
        status=AnswerStatus.ANSWERED,
    )

    retriever = FakeRetriever(documents=[irrelevant_local_doc])
    grader = FakeRelevanceGrader(default_is_relevant=False)
    query_rewriter = FakeQueryRewriter(rewritten_question=rewritten_query)
    web_search_provider = FakeWebSearchProvider(documents=[web_doc])
    generator = FakeGenerator(answers=[candidate_1, candidate_2])
    checker = FakeHallucinationChecker(results=[False, False])

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        query_rewriter=query_rewriter,
        generator=generator,
        web_search_provider=web_search_provider,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    result = graph.invoke(create_initial_state(question))

    # 1. Trace step order assertion
    trace_step_names = [step.name for step in result["trace"].steps]
    assert trace_step_names == [
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

    # 2. State assertions
    assert result["question"] == question
    assert result["rewritten_question"] == rewritten_query
    assert result["documents"] == [web_doc]
    assert result["generation_attempts"] == 2
    assert result["is_supported"] is False

    # 3. Safe refusal answer assertions
    final_answer = result["answer"]
    assert final_answer is not None
    assert final_answer.status == AnswerStatus.UNSUPPORTED
    assert final_answer.text == "I cannot provide a supported answer based on the available evidence."
    assert final_answer != candidate_1
    assert final_answer != candidate_2

    # 4. Attempt call counts
    assert len(generator.received_calls) == 2
    assert len(checker.received_checks) == 2


def test_successful_regeneration_retry() -> None:
    """Verifies that a second generation attempt succeeds if grounding passes."""
    question = Question(text="How do I check pod status?")
    doc = Document(content="Use kubectl get pods to view pod status.", source="docs/status.md")

    candidate_unsupported = Answer(text="Use kubectl status pods", status=AnswerStatus.ANSWERED)
    candidate_supported = Answer(text="Use kubectl get pods to check status.", status=AnswerStatus.ANSWERED)

    retriever = FakeRetriever(documents=[doc])
    grader = FakeRelevanceGrader(default_is_relevant=True)
    query_rewriter = FakeQueryRewriter()
    web_search_provider = FakeWebSearchProvider()
    generator = FakeGenerator(answers=[candidate_unsupported, candidate_supported])
    checker = FakeHallucinationChecker(results=[False, True])

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        query_rewriter=query_rewriter,
        generator=generator,
        web_search_provider=web_search_provider,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    result = graph.invoke(create_initial_state(question))

    trace_step_names = [step.name for step in result["trace"].steps]
    assert trace_step_names == [
        "retrieve",
        "grade_documents",
        "generate",
        "hallucination_check",
        "generate",
        "hallucination_check",
    ]
    assert "safe_refusal" not in trace_step_names

    assert result["answer"] == candidate_supported
    assert result["answer"].status == AnswerStatus.ANSWERED
    assert result["is_supported"] is True
    assert result["generation_attempts"] == 2
    assert len(generator.received_calls) == 2
    assert len(checker.received_checks) == 2


def test_immediate_success_single_attempt() -> None:
    """Verifies that a grounded first candidate exits immediately without retries."""
    question = Question(text="How do I check pod status?")
    doc = Document(content="Use kubectl get pods", source="docs/status.md")
    expected_answer = Answer(text="Use kubectl get pods.", status=AnswerStatus.ANSWERED)

    retriever = FakeRetriever(documents=[doc])
    grader = FakeRelevanceGrader(default_is_relevant=True)
    query_rewriter = FakeQueryRewriter()
    web_search_provider = FakeWebSearchProvider()
    generator = FakeGenerator(answer=expected_answer)
    checker = FakeHallucinationChecker(is_supported=True)

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        query_rewriter=query_rewriter,
        generator=generator,
        web_search_provider=web_search_provider,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    result = graph.invoke(create_initial_state(question))

    trace_step_names = [step.name for step in result["trace"].steps]
    assert trace_step_names == [
        "retrieve",
        "grade_documents",
        "generate",
        "hallucination_check",
    ]
    assert result["generation_attempts"] == 1
    assert len(generator.received_calls) == 1
    assert len(checker.received_checks) == 1


def test_retry_budget_termination_guarantee() -> None:
    """Verifies that generator calls strictly terminate at MAX_GENERATION_ATTEMPTS."""
    question = Question(text="Unanswerable question")
    doc = Document(content="Irrelevant text", source="doc")

    retriever = FakeRetriever(documents=[doc])
    grader = FakeRelevanceGrader(default_is_relevant=True)
    query_rewriter = FakeQueryRewriter()
    web_search_provider = FakeWebSearchProvider()
    generator = FakeGenerator()
    checker = FakeHallucinationChecker(results=[False, False, False])

    deps = WorkflowDependencies(
        retriever=retriever,
        relevance_grader=grader,
        query_rewriter=query_rewriter,
        generator=generator,
        web_search_provider=web_search_provider,
        hallucination_checker=checker,
    )

    graph = build_graph(deps)
    result = graph.invoke(create_initial_state(question))

    assert len(generator.received_calls) == MAX_GENERATION_ATTEMPTS
    assert len(checker.received_checks) == MAX_GENERATION_ATTEMPTS
    assert result["generation_attempts"] == MAX_GENERATION_ATTEMPTS
    assert result["answer"].status == AnswerStatus.UNSUPPORTED
