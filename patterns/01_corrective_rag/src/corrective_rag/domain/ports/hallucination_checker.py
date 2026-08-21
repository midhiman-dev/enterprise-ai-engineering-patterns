"""Hallucination Checker Domain Port.

Defines the capability contract for verifying whether a candidate answer is
supported by (grounded in) the provided evidence documents.
"""

from collections.abc import Sequence
from typing import Protocol

from corrective_rag.domain.entities.answer import Answer
from corrective_rag.domain.entities.document import Document


class HallucinationChecker(Protocol):
    """Port for verifying candidate answer grounding against evidence documents.

    This capability is isolated behind a Domain port so that grounding validation
    strategies can evolve without impacting workflow orchestration.
    """

    def is_supported(
        self,
        answer: Answer,
        documents: Sequence[Document],
    ) -> bool:
        """Determine whether an answer is supported by the evidence documents.

        Args:
            answer: Candidate answer to evaluate.
            documents: Sequence of evidence documents used to ground the answer.

        Returns:
            True if the answer is supported by the evidence, False otherwise.
        """
        ...
