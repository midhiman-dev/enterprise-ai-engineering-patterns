"""Grade Documents Node Handler.

Evaluates retrieved documents using the RelevanceGrader domain port, filtering out
irrelevant documents so generation proceeds only with relevant evidence.
"""

from typing import Callable

from corrective_rag.application.graph_state import GraphState
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.graded_document import GradedDocument


def make_grade_documents_node(
    deps: WorkflowDependencies,
) -> Callable[[GraphState], dict]:
    """Factory creating the grade_documents node handler with injected dependencies.

    Args:
        deps: Workflow dependencies containing the RelevanceGrader port.

    Returns:
        Callable node handler compatible with LangGraph.
    """

    def grade_documents(state: GraphState) -> dict:
        question = state["question"]
        candidate_docs = state["documents"]

        graded_docs: list[GradedDocument] = []
        relevant_docs = []

        for doc in candidate_docs:
            graded_doc = deps.relevance_grader.grade(question, doc)
            graded_docs.append(graded_doc)
            if graded_doc.is_relevant:
                relevant_docs.append(doc)

        state["trace"].add_step(
            name="grade_documents",
            detail=f"{len(relevant_docs)} of {len(candidate_docs)} documents marked relevant",
        )

        return {
            "graded_documents": graded_docs,
            "documents": relevant_docs,
        }

    return grade_documents
