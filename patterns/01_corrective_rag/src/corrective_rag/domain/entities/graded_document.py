"""GradedDocument entity representing document relevance evaluation."""

from dataclasses import dataclass

from corrective_rag.domain.entities.document import Document


@dataclass(frozen=True)
class GradedDocument:
    """Represents a Document after relevance evaluation.

    Encapsulates the core domain decision of whether a document is relevant
    to a given question, along with optional evaluation details.

    Note on Score Semantics:
        `score` represents optional supporting numeric metadata (e.g., probability,
        cosine similarity, reranker logit). The Domain layer does not impose an
        arbitrary range contract (such as [0, 1]) on scores to remain adapter-agnostic.
    """

    document: Document
    is_relevant: bool
    score: float | None = None
    reason: str | None = None
