"""GradedDocument entity representing document relevance evaluation."""

from dataclasses import dataclass

from corrective_rag.domain.entities.document import Document


@dataclass(frozen=True)
class GradedDocument:
    """Represents a Document after relevance evaluation.

    Encapsulates the core domain decision of whether a document is relevant
    to a given question, along with optional evaluation details.

    Invariants:
        - document must be a valid Document instance.
        - if score is provided, it must be between 0.0 and 1.0 inclusive.
    """

    document: Document
    is_relevant: bool
    score: float | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.score is not None:
            if not (0.0 <= self.score <= 1.0):
                raise ValueError(
                    f"Graded document score must be between 0.0 and 1.0, got {self.score}"
                )
