"""Domain Entities package.

Provides pure Python domain entities representing data and decisions
in the Corrective RAG workflow. Zero third-party SDK dependencies.
"""

from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.decision_trace import DecisionTrace, TraceStep
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.graded_document import GradedDocument
from corrective_rag.domain.entities.question import Question

__all__ = [
    "Answer",
    "AnswerStatus",
    "DecisionTrace",
    "Document",
    "GradedDocument",
    "Question",
    "TraceStep",
]
