"""Document entity representing provider-neutral evidence."""

from dataclasses import dataclass, field
from datetime import date, datetime
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Document:
    """Represents a retrieved document or piece of evidence.

    Designed to be provider-neutral, supporting both local Kubernetes knowledge-base
    evidence and web search evidence without vendor-specific fields.

    Note on Immutability:
        `@dataclass(frozen=True)` prevents rebinding fields. In addition, `metadata`
        is defensively copied and wrapped in a read-only `MappingProxyType` during
        initialization to provide shallow immutability against caller dictionary mutation.
        Nested mutable objects inside metadata are not recursively frozen.

    Invariants:
        - content must not be empty or whitespace-only.
        - source must not be empty or whitespace-only.
    """

    content: str
    source: str
    title: str | None = None
    source_url: str | None = None
    snapshot_date: date | datetime | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("Document content cannot be empty or whitespace-only.")
        if not self.source or not self.source.strip():
            raise ValueError("Document source cannot be empty or whitespace-only.")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
