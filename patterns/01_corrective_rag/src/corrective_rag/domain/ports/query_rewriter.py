"""Query Rewriter Domain Port.

Defines the capability contract for rewriting a user's question into a more
effective formulation for retrieval or external search when local evidence is
insufficient.
"""

from typing import Protocol

from corrective_rag.domain.entities.question import Question


class QueryRewriter(Protocol):
    """Port for rewriting questions for optimized retrieval.

    This capability is isolated behind a Domain port to decouple query reformulations
    (e.g., LLM rewriters) from the orchestration workflow.
    """

    def rewrite(self, question: Question) -> Question:
        """Rewrite a question into a refined natural-language retrieval question.

        Args:
            question: The original user question.

        Returns:
            A new Question entity containing the rewritten query text.
        """
        ...
