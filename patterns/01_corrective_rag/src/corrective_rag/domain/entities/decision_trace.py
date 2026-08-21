"""DecisionTrace entity for execution auditability and step tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True)
class TraceStep:
    """Represents a single recorded step within a decision trace.

    Invariants:
        - name must not be empty or whitespace-only.
    """

    name: str
    detail: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("TraceStep name cannot be empty or whitespace-only.")


@dataclass
class DecisionTrace:
    """Represents an ordered trace of execution steps for auditability and UI inspection.

    Note on Mutability Design:
        `DecisionTrace` is intentionally mutable via controlled step registration (`add_step`).
        This reflects its domain role as an active execution audit log during workflow progression,
        avoiding artificial copy-on-write collection manipulation while preserving step order.
    """

    _steps: list[TraceStep] = field(default_factory=list)

    @property
    def steps(self) -> Sequence[TraceStep]:
        """Returns an immutable view of the recorded execution steps."""
        return tuple(self._steps)

    def add_step(self, name: str, detail: str | None = None) -> TraceStep:
        """Appends a new step to the trace and returns it."""
        step = TraceStep(name=name, detail=detail)
        self._steps.append(step)
        return step

    def __len__(self) -> int:
        return len(self._steps)
