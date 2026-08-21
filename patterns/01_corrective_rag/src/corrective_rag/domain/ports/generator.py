"""Generator Domain Port.

Defines the capability contract for generating a candidate answer grounded in
supplied evidence documents.
"""

from collections.abc import Sequence
from typing import Protocol

from corrective_rag.domain.entities.answer import Answer
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question


class Generator(Protocol):
    """Port for candidate answer generation grounded in evidence documents.

    This capability is isolated behind a Domain port to keep specific LLM SDKs
    (OpenAI, Ollama) and prompts outside the application layer.
    """

    def generate(
        self,
        question: Question,
        documents: Sequence[Document],
    ) -> Answer:
        """Generate a candidate answer grounded in the provided documents.

        Args:
            question: User's question to answer.
            documents: Ordered sequence of evidence documents.

        Returns:
            An Answer entity representing the generated candidate response.
        """
        ...
