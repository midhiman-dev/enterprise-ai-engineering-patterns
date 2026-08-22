"""Document loader for local Knowledge-Base fixture documents."""

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class SourceDocument:
    """Internal infrastructure representation of an un-chunked source document.

    Attributes:
        content: Raw text content of the document.
        source: Provenance path or file identifier.
        metadata: Read-only mapping of file or document attributes.
    """

    content: str
    source: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("SourceDocument content cannot be empty or whitespace-only.")
        if not self.source or not self.source.strip():
            raise ValueError("SourceDocument source cannot be empty or whitespace-only.")

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


def _extract_title(content: str, default_title: str) -> str:
    """Extract first top-level Markdown header title if available."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return default_title


def load_documents_from_directory(directory_path: str | Path) -> list[SourceDocument]:
    """Load Markdown and text documents from a directory into SourceDocument instances.

    Args:
        directory_path: Path to the directory containing fixture files.

    Returns:
        List of loaded SourceDocument instances sorted by filename.

    Raises:
        FileNotFoundError: If directory_path does not exist.
        NotADirectoryError: If directory_path is not a directory.
    """
    path = Path(directory_path)
    if not path.exists():
        raise FileNotFoundError(f"Source document directory '{directory_path}' does not exist.")
    if not path.is_dir():
        raise NotADirectoryError(f"Path '{directory_path}' is not a directory.")

    documents: list[SourceDocument] = []
    supported_extensions = {".md", ".txt"}

    # Sort files for deterministic loading order
    for file_path in sorted(path.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            content = file_path.read_text(encoding="utf-8").strip()
            if not content:
                continue

            file_stem = file_path.stem
            title = _extract_title(content, file_stem)
            source_id = file_path.name

            metadata: dict[str, object] = {
                "document_title": title,
                "file_name": file_path.name,
                "file_extension": file_path.suffix.lower(),
            }

            documents.append(
                SourceDocument(
                    content=content,
                    source=source_id,
                    metadata=metadata,
                )
            )

    return documents
