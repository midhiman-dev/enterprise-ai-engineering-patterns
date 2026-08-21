"""Relevance Grader Domain Port.

Defines the capability contract for evaluating whether a retrieved document is
relevant to a user's question.
"""

from typing import Protocol

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.graded_document import GradedDocument
from corrective_rag.domain.entities.question import Question


class RelevanceGrader(Protocol):
    """Port for evaluating document relevance to a question.

    This capability is isolated behind a Domain port so that document grading
    logic (LLM prompt/structured output) is abstracted away from application
    orchestration.
    """

    def grade(
        self,
        question: Question,
        document: Document,
    ) -> GradedDocument:
        """Grade the relevance of a single candidate document to a question.

        Args:
            question: The user's question.
            document: Candidate document to evaluate.

        Returns:
            A GradedDocument entity containing relevance decision and optional score/reasoning.
        """
        ...
