"""Decision Trace Repository Domain Port.

Defines the capability contract for persisting execution decision traces recorded
during workflow processing.
"""

from typing import Protocol

from corrective_rag.domain.entities.decision_trace import DecisionTrace


class DecisionTraceRepository(Protocol):
    """Port for persisting workflow decision traces.

    This capability is isolated behind a Domain port to keep persistence mechanisms
    (e.g., SQLite, PostgreSQL) separate from core domain logic.
    """

    def save(self, trace: DecisionTrace) -> None:
        """Persist a decision trace.

        Args:
            trace: The DecisionTrace entity to save.
        """
        ...
