"""LangGraph Application State definition.

GraphState represents the transient orchestration state maintained by LangGraph
during execution of the Corrective RAG workflow.

Architectural Boundary Rationale:
    GraphState lives in the Application layer, NOT the Domain layer.
    Domain entities (Question, Document, Answer, DecisionTrace) represent core domain concepts
    and business rules. GraphState is an orchestration mechanism tracking step progression,
    intermediate execution data, and state transitions within LangGraph.
"""

from typing import TypedDict

from corrective_rag.domain.entities.answer import Answer
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.graded_document import GradedDocument
from corrective_rag.domain.entities.question import Question


class GraphState(TypedDict):
    """Orchestration state passed between LangGraph workflow nodes.

    Attributes:
        question: The user's input question being answered.
        rewritten_question: Search reformulation of user question for external search (None if not rewritten).
        documents: The current set of documents (initially retrieved, filtered, or web search evidence).
        graded_documents: Evaluation results for each candidate document from relevance grading.
        answer: The candidate answer generated from evidence documents (None until generated).
        is_supported: Grounding verification result (None until checked).
        trace: Mutable audit log tracking execution steps.
    """

    question: Question
    rewritten_question: Question | None
    documents: list[Document]
    graded_documents: list[GradedDocument]
    answer: Answer | None
    is_supported: bool | None
    trace: DecisionTrace
