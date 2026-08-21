"""Generate Node Handler.

Generates a candidate answer grounded in relevant evidence documents using the Generator domain port.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies


def make_generate_node(
    deps: WorkflowDependencies,
) -> Callable[[GraphState], dict]:
    """Factory creating the generate node handler with injected dependencies.

    Args:
        deps: Workflow dependencies containing the Generator port.

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def generate(state: GraphState) -> dict:
        question = state["question"]
        evidence_docs = state["documents"]
        attempts = state.get("generation_attempts", 0) + 1

        answer = deps.generator.generate(question, evidence_docs)

        state["trace"].add_step(
            name="generate",
            detail=f"Generated candidate answer from {len(evidence_docs)} documents (attempt {attempts})",
        )

        return {
            "answer": answer,
            "generation_attempts": attempts,
        }

    return generate
