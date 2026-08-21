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
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.question import Question


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
        "documents": [],
        "graded_documents": [],
        "answer": None,
        "is_supported": None,
        "trace": trace if trace is not None else DecisionTrace(),
    }


def build_graph(dependencies: WorkflowDependencies) -> CompiledStateGraph:
    """Builds and compiles the straight-path Pass-3 Corrective RAG state graph.

    Graph Topology:
        START -> retrieve -> grade_documents -> generate -> hallucination_check -> END

    Args:
        dependencies: Explicit container of domain ports.

    Returns:
        Compiled StateGraph executable instance.
    """
    workflow = StateGraph(GraphState)

    # Register nodes using dependency-injected factories
    workflow.add_node("retrieve", make_retrieve_node(dependencies))
    workflow.add_node("grade_documents", make_grade_documents_node(dependencies))
    workflow.add_node("generate", make_generate_node(dependencies))
    workflow.add_node("hallucination_check", make_hallucination_check_node(dependencies))

    # Add straight execution edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("grade_documents", "generate")
    workflow.add_edge("generate", "hallucination_check")
    workflow.add_edge("hallucination_check", END)

    return workflow.compile()
