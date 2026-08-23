"""Executable Application runtime boundary bundling state graph orchestration and trace persistence.

Demonstrates Clean Architecture application entry point where compiled LangGraph state graph
and DecisionTraceRepository port are owned together as a cohesive application instance.
"""

from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.use_cases.run_workflow import run_workflow
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.question import Question
from corrective_rag.domain.ports.decision_trace_repository import DecisionTraceRepository


@dataclass(frozen=True)
class CorrectiveRAGApplication:
    """Executable Corrective RAG Application runtime boundary.

    Bundles the compiled orchestration graph and the DecisionTraceRepository port,
    ensuring that executing the workflow automatically persists the decision trace exactly once.

    Attributes:
        graph: Compiled state graph defining node handlers and conditional routing topology.
        repository: DecisionTraceRepository port interface for persisting execution audit traces.
    """

    graph: CompiledStateGraph
    repository: DecisionTraceRepository

    def run(
        self,
        question: Question,
        trace: DecisionTrace | None = None,
    ) -> GraphState:
        """Executes the workflow for a given question and persists the completed decision trace.

        Args:
            question: User's input question entity.
            trace: Optional existing DecisionTrace instance. If None, a new trace is initialized.

        Returns:
            Final GraphState dictionary resulting from workflow execution.

        Raises:
            RuntimeError: If decision trace persistence fails.
        """
        return run_workflow(
            graph=self.graph,
            question=question,
            repository=self.repository,
            trace=trace,
        )
