"""Answer entity representing the final application output."""

from dataclasses import dataclass
from enum import Enum


class AnswerStatus(str, Enum):
    """Represents the status outcome of an answer."""

    ANSWERED = "answered"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class Answer:
    """Represents the final answer returned to the user.

    Distinguishes between a grounded, successful answer and an explicit safe
    refusal explanation when available evidence is insufficient.

    Invariants:
        - text must not be empty or whitespace-only for any AnswerStatus.
    """

    text: str
    status: AnswerStatus = AnswerStatus.ANSWERED

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("Answer text cannot be empty or whitespace-only.")
