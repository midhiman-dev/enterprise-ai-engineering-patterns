"""Retrieve Node Handler.

Queries the Retriever domain port for candidate documents relevant to the user's question.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies


def make_retrieve_node(
    deps: WorkflowDependencies,
) -> Callable[[GraphState], dict]:
    """Factory creating the retrieve node handler with injected dependencies.

    Args:
        deps: Workflow dependencies containing the Retriever port.

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def retrieve(state: GraphState) -> dict:
        question = state["question"]
        candidate_docs = list(deps.retriever.retrieve(question))

        state["trace"].add_step(
            name="retrieve",
            detail=f"Retrieved {len(candidate_docs)} candidate documents",
        )

        return {"documents": candidate_docs}

    return retrieve
