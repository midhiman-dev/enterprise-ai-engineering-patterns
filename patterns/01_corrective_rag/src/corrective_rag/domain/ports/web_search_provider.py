"""Web Search Provider Domain Port.

Defines the capability contract for searching external web sources to gather
up-to-date evidence when local knowledge is insufficient or stale.
"""

from collections.abc import Sequence
from typing import Protocol

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question


class WebSearchProvider(Protocol):
    """Port for searching external web sources.

    This capability is isolated behind a Domain port to ensure external search
    APIs (e.g. Tavily) remain decoupled from domain and application logic.
    """

    def search(self, question: Question) -> Sequence[Document]:
        """Search external web sources for evidence relevant to the question.

        Args:
            question: Natural language question to search on the web.

        Returns:
            An ordered sequence of candidate documents retrieved from external sources.
        """
        ...
