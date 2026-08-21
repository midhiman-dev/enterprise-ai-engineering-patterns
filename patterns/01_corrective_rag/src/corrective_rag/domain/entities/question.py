"""Question entity representing a user's troubleshooting query."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    """Represents a user troubleshooting query.

    Invariants:
        - text must not be empty or whitespace-only.
        - preserves exact original user wording without silent modification.
    """

    text: str

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("Question text cannot be empty or whitespace-only.")
