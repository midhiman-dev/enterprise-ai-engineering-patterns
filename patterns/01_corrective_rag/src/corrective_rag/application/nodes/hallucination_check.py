"""Hallucination Check Node Handler.

Verifies candidate answer grounding against evidence documents using the HallucinationChecker domain port.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies


def make_hallucination_check_node(
    deps: WorkflowDependencies,
) -> Callable[[GraphState], dict]:
    """Factory creating the hallucination_check node handler with injected dependencies.

    Args:
        deps: Workflow dependencies containing the HallucinationChecker port.

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def hallucination_check(state: GraphState) -> dict:
        answer = state["answer"]
        evidence_docs = state["documents"]

        if answer is None:
            raise ValueError("Cannot perform hallucination check on None answer.")

        is_supported = deps.hallucination_checker.is_supported(answer, evidence_docs)

        state["trace"].add_step(
            name="hallucination_check",
            detail=f"supported={is_supported}",
        )

        return {"is_supported": is_supported}

    return hallucination_check
