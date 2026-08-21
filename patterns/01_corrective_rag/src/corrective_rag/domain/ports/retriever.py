"""Retriever Domain Port.

Defines the capability contract for retrieving candidate documents from a local
knowledge source (e.g. vector database snapshot) for a user's question.
"""

from collections.abc import Sequence
from typing import Protocol

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question


class Retriever(Protocol):
    """Port for candidate document retrieval from local knowledge sources.

    This capability is isolated behind a Domain port so that application
    orchestration depends on document retrieval behavior rather than concrete
    vector databases like Chroma.
    """

    def retrieve(self, question: Question) -> Sequence[Document]:
        """Retrieve candidate documents relevant to the given question.

        Args:
            question: Natural language question to query local knowledge.

        Returns:
            An ordered sequence of candidate documents.
        """
        ...
