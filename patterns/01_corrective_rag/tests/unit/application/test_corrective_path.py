"""Unit tests for the Pass-4 LangGraph corrective web-fallback execution path."""

from corrective_rag.application.workflow import build_graph, create_initial_state
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


def test_corrective_path_execution_golden_query_2() -> None:
    """Core Pass-4 Acceptance Test: Verifies corrective web-fallback workflow execution.

    Golden Query 2: How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?
    Path: START -> retrieve -> grade_documents -> rewrite_query -> web_search -> generate -> hallucination_check -> END
    """
    original_question = Question(
        text="How do I handle pod eviction under Kubernetes 1.32's new node-pressure eviction policy?"
    )
    stale_local_doc = Document(
        content="Kubernetes 1.28 node eviction policy documentation snapshot.",
        source="k8s_snapshot_1.28/eviction.md",
    )
    rewritten_question = Question(
        text="Kubernetes 1.32 node pressure eviction policy pod eviction changes"
    )
    web_doc1 = Document(
        content="Kubernetes 1.32 introduced updated node-pressure eviction thresholds for system reserves.",
        source="https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/",
    )
    web_doc2 = Document(
        content="To handle pod eviction under 1.32, set soft eviction thresholds and grace periods in kubelet config.",
        source="https://kubernetes.io/docs/tasks/administer-cluster/out-of-resource/",
    )
    expected_answer = Answer(
        text="Configure soft eviction thresholds and grace periods in Kubelet configuration under Kubernetes 1.32.",
        status=AnswerStatus.ANSWERED,
    )

    retriever = FakeRetriever(documents=[stale_local_doc])
    grader = FakeRelevanceGrader(default_is_relevant=False)
    query_rewriter = FakeQueryRewriter(rewritten_question=rewritten_question)
    web_search_provider = FakeWebSearchProvider(documents=[web_doc1, web_doc2])
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
    result = graph.invoke(create_initial_state(original_question))

    # 1. State assertions
    assert result["question"] == original_question
    assert result["rewritten_question"] == rewritten_question
    assert result["documents"] == [web_doc1, web_doc2]
    assert len(result["graded_documents"]) == 1
    assert result["graded_documents"][0].is_relevant is False
    assert result["answer"] == expected_answer
    assert result["is_supported"] is True

    # 2. DecisionTrace step order assertion
    trace_step_names = [step.name for step in result["trace"].steps]
    assert trace_step_names == [
        "retrieve",
        "grade_documents",
        "rewrite_query",
        "web_search",
        "generate",
        "hallucination_check",
    ]

    # 3. Port invocation input/output assertions
    assert retriever.received_questions == [original_question]
    assert grader.received_grades == [(original_question, stale_local_doc)]
    assert query_rewriter.received_questions == [original_question]
    assert web_search_provider.received_questions == [rewritten_question]

    # Generator received ORIGINAL question + WEB documents
    assert len(generator.received_calls) == 1
    gen_question, gen_docs = generator.received_calls[0]
    assert gen_question == original_question
    assert gen_docs == (web_doc1, web_doc2)

    # Hallucination checker received candidate answer + WEB documents
    assert len(checker.received_checks) == 1
    chk_answer, chk_docs = checker.received_checks[0]
    assert chk_answer == expected_answer
    assert chk_docs == (web_doc1, web_doc2)


def test_routing_decision_boundary_local_relevance() -> None:
    """Verifies that local evidence sufficiency directly dictates the workflow route."""
    question = Question(text="What is a Pod?")
    local_doc = Document(content="A Pod is the smallest deployable object in K8s.", source="k8s_pod.md")
    web_doc = Document(content="Web doc about Pods", source="web_pod.md")

    # Scenario A: At least 1 relevant local doc -> straight path
    retriever_a = FakeRetriever(documents=[local_doc])
    grader_a = FakeRelevanceGrader(default_is_relevant=True)
    rewriter_a = FakeQueryRewriter()
    web_search_a = FakeWebSearchProvider(documents=[web_doc])
    generator_a = FakeGenerator()
    checker_a = FakeHallucinationChecker(is_supported=True)

    deps_a = WorkflowDependencies(
        retriever=retriever_a,
        relevance_grader=grader_a,
        query_rewriter=rewriter_a,
        generator=generator_a,
        web_search_provider=web_search_a,
        hallucination_checker=checker_a,
    )

    graph_a = build_graph(deps_a)
    result_a = graph_a.invoke(create_initial_state(question))

    trace_a = [step.name for step in result_a["trace"].steps]
    assert trace_a == ["retrieve", "grade_documents", "generate", "hallucination_check"]
    assert result_a["documents"] == [local_doc]
    assert rewriter_a.received_questions == []
    assert web_search_a.received_questions == []

    # Scenario B: 0 relevant local docs -> corrective path
    retriever_b = FakeRetriever(documents=[local_doc])
    grader_b = FakeRelevanceGrader(default_is_relevant=False)
    rewriter_b = FakeQueryRewriter()
    web_search_b = FakeWebSearchProvider(documents=[web_doc])
    generator_b = FakeGenerator()
    checker_b = FakeHallucinationChecker(is_supported=True)

    deps_b = WorkflowDependencies(
        retriever=retriever_b,
        relevance_grader=grader_b,
        query_rewriter=rewriter_b,
        generator=generator_b,
        web_search_provider=web_search_b,
        hallucination_checker=checker_b,
    )

    graph_b = build_graph(deps_b)
    result_b = graph_b.invoke(create_initial_state(question))

    trace_b = [step.name for step in result_b["trace"].steps]
    assert trace_b == [
        "retrieve",
        "grade_documents",
        "rewrite_query",
        "web_search",
        "generate",
        "hallucination_check",
    ]
    assert result_b["documents"] == [web_doc]
    assert len(rewriter_b.received_questions) == 1
    assert len(web_search_b.received_questions) == 1
