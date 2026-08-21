"""Web Search Node Handler.

Invokes the WebSearchProvider domain port using the rewritten question to retrieve
external evidence documents when local knowledge is insufficient.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies


def make_web_search_node(
    deps: WorkflowDependencies,
) -> Callable[[GraphState], dict]:
    """Factory creating the web_search node handler with injected dependencies.

    Args:
        deps: Workflow dependencies containing the WebSearchProvider port.

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def web_search(state: GraphState) -> dict:
        rewritten_question = state.get("rewritten_question")
        if rewritten_question is None:
            raise ValueError("Cannot execute web search without a rewritten question.")

        web_docs = list(deps.web_search_provider.search(rewritten_question))

        state["trace"].add_step(
            name="web_search",
            detail=f"Retrieved {len(web_docs)} web documents",
        )

        return {"documents": web_docs}

    return web_search
