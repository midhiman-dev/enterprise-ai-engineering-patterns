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

    Distinguishes between a grounded, successful answer and a safe refusal
    or unsupported answer when available evidence is insufficient.

    Invariants:
        - text must not be empty or whitespace-only when status is ANSWERED.
    """

    text: str
    status: AnswerStatus = AnswerStatus.ANSWERED

    def __post_init__(self) -> None:
        if self.status == AnswerStatus.ANSWERED and (not self.text or not self.text.strip()):
            raise ValueError("Answer text cannot be blank when status is ANSWERED.")
