"""Rewrite Query Node Handler.

Invokes the QueryRewriter domain port to reformulate the user's question for web search
when local retrieval evidence is insufficient.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies


def make_rewrite_query_node(
    deps: WorkflowDependencies,
) -> Callable[[GraphState], dict]:
    """Factory creating the rewrite_query node handler with injected dependencies.

    Args:
        deps: Workflow dependencies containing the QueryRewriter port.

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def rewrite_query(state: GraphState) -> dict:
        question = state["question"]
        rewritten = deps.query_rewriter.rewrite(question)

        state["trace"].add_step(
            name="rewrite_query",
            detail="Rewrote question for external search",
        )

        return {"rewritten_question": rewritten}

    return rewrite_query
