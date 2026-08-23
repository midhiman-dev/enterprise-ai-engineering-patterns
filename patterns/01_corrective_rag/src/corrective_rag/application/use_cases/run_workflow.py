"""Application Use Case for executing the Corrective RAG workflow.

Orchestrates state graph execution and ensures the recorded DecisionTrace audit record
is persisted at the completion of workflow execution.
"""

from langgraph.graph.state import CompiledStateGraph

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow import create_initial_state
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.question import Question
from corrective_rag.domain.ports.decision_trace_repository import DecisionTraceRepository


def run_workflow(
    graph: CompiledStateGraph,
    question: Question,
    repository: DecisionTraceRepository | None = None,
    trace: DecisionTrace | None = None,
) -> GraphState:
    """Executes the compiled Corrective RAG state graph and persists the decision trace upon completion.

    Args:
        graph: Compiled StateGraph executable instance.
        question: User's input question entity.
        repository: Optional DecisionTraceRepository port for persisting execution audit trace.
        trace: Optional existing DecisionTrace instance. If None, a new trace is created.

    Returns:
        Final GraphState dictionary resulting from workflow completion.

    Raises:
        RuntimeError: If decision trace persistence fails.
    """
    initial_state = create_initial_state(question, trace=trace)
    final_state: GraphState = graph.invoke(initial_state)

    if repository is not None:
        completed_trace = final_state["trace"]
        repository.save(completed_trace)

    return final_state
