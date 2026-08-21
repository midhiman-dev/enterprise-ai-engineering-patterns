"""Corrective RAG LangGraph Workflow Builder.

Assembles the Application state graph for the Pass-3 straight-path execution.
This module directly demonstrates LangGraph constructs (StateGraph, nodes, edges, compile)
without hiding the orchestration framework behind custom abstract wrappers.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.nodes.generate import make_generate_node
from corrective_rag.application.nodes.grade_documents import make_grade_documents_node
from corrective_rag.application.nodes.hallucination_check import make_hallucination_check_node
from corrective_rag.application.nodes.retrieve import make_retrieve_node
from corrective_rag.application.nodes.rewrite_query import make_rewrite_query_node
from corrective_rag.application.nodes.safe_refusal import make_safe_refusal_node
from corrective_rag.application.nodes.web_search import make_web_search_node
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.question import Question

MAX_GENERATION_ATTEMPTS = 2


def create_initial_state(
    question: Question,
    trace: DecisionTrace | None = None,
) -> GraphState:
    """Helper to construct a valid initial GraphState dictionary.

    Args:
        question: User's input question.
        trace: Optional existing DecisionTrace instance. If None, a new trace is initialized.

    Returns:
        GraphState dictionary ready for graph invocation.
    """
    return {
        "question": question,
        "rewritten_question": None,
        "documents": [],
        "graded_documents": [],
        "answer": None,
        "is_supported": None,
        "generation_attempts": 0,
        "trace": trace if trace is not None else DecisionTrace(),
    }


def route_after_grading(state: GraphState) -> str:
    """Pure conditional routing function evaluated after document grading.

    Determines whether local retrieval evidence is sufficient to generate an answer
    or if the workflow must rewrite the query and perform external web search.

    Args:
        state: Current GraphState after grade_documents execution.

    Returns:
        "generate" if relevant local documents exist, otherwise "rewrite_query".
    """
    if state["documents"]:
        return "generate"
    return "rewrite_query"


def route_after_hallucination_check(state: GraphState) -> str:
    """Pure conditional routing function evaluated after hallucination check.

    Determines whether the generated answer is grounded/supported by evidence,
    or if the workflow should attempt regeneration or trigger safe refusal.

    Args:
        state: Current GraphState after hallucination_check execution.

    Returns:
        "end" if supported, "generate" if retry budget remains, otherwise "safe_refusal".
    """
    if state["is_supported"]:
        return "end"

    if state.get("generation_attempts", 0) < MAX_GENERATION_ATTEMPTS:
        return "generate"

    return "safe_refusal"


def build_graph(dependencies: WorkflowDependencies) -> CompiledStateGraph:
    """Builds and compiles the Pass-5 Corrective RAG state graph with retry & refusal routing.

    Graph Topology:
        START -> retrieve -> grade_documents
                    ├── relevant docs -> generate -> hallucination_check ──┐
                    └── no relevant docs -> rewrite_query -> web_search -> generate -> hallucination_check ──┤
                                                                                                              │
                                                   ┌──────────────────────────────────────────────────────────┘
                                                   │
                                                   ├── supported → END
                                                   ├── retry budget left → generate
                                                   └── budget exhausted → safe_refusal → END

    Args:
        dependencies: Explicit container of domain ports.

    Returns:
        Compiled StateGraph executable instance.
    """
    workflow = StateGraph(GraphState)

    # Register nodes using dependency-injected factories
    workflow.add_node("retrieve", make_retrieve_node(dependencies))
    workflow.add_node("grade_documents", make_grade_documents_node(dependencies))
    workflow.add_node("rewrite_query", make_rewrite_query_node(dependencies))
    workflow.add_node("web_search", make_web_search_node(dependencies))
    workflow.add_node("generate", make_generate_node(dependencies))
    workflow.add_node("hallucination_check", make_hallucination_check_node(dependencies))
    workflow.add_node("safe_refusal", make_safe_refusal_node(dependencies))

    # Add workflow execution edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    # Add conditional branching based on local evidence sufficiency
    workflow.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {
            "generate": "generate",
            "rewrite_query": "rewrite_query",
        },
    )

    workflow.add_edge("rewrite_query", "web_search")
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", "hallucination_check")

    # Add conditional branching after hallucination verification
    workflow.add_conditional_edges(
        "hallucination_check",
        route_after_hallucination_check,
        {
            "end": END,
            "generate": "generate",
            "safe_refusal": "safe_refusal",
        },
    )

    workflow.add_edge("safe_refusal", END)

    return workflow.compile()
