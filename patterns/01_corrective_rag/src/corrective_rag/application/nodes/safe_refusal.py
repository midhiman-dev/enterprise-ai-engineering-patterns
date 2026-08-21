"""Safe Refusal Node Handler.

Executes when the generation retry budget is exhausted and the candidate answer remains unsupported
by evidence, returning a deterministic refusal answer with AnswerStatus.UNSUPPORTED.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.answer import Answer, AnswerStatus


def make_safe_refusal_node(
    deps: WorkflowDependencies | None = None,
) -> Callable[[GraphState], dict]:
    """Factory creating the safe_refusal node handler.

    Args:
        deps: Optional WorkflowDependencies (accepted for uniform factory signature).

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def safe_refusal(state: GraphState) -> dict:
        refusal_answer = Answer(
            text="I cannot provide a supported answer based on the available evidence.",
            status=AnswerStatus.UNSUPPORTED,
        )

        state["trace"].add_step(
            name="safe_refusal",
            detail="Retry budget exhausted; returning unsupported answer",
        )

        return {"answer": refusal_answer}

    return safe_refusal
