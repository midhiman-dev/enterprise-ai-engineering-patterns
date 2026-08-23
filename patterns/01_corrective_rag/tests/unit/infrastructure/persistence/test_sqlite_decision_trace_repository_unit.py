"""Unit tests for SQLiteDecisionTraceRepository infrastructure adapter."""

from pathlib import Path

import pytest

from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.ports.decision_trace_repository import DecisionTraceRepository
from corrective_rag.infrastructure.persistence.sqlite_decision_trace_repository import (
    SQLiteDecisionTraceRepository,
)


def test_sqlite_repository_initialization_validation() -> None:
    """Verifies that empty or whitespace-only db_path raises ValueError."""
    with pytest.raises(ValueError, match="db_path cannot be empty"):
        SQLiteDecisionTraceRepository(db_path="")

    with pytest.raises(ValueError, match="db_path cannot be empty"):
        SQLiteDecisionTraceRepository(db_path="   ")


def test_sqlite_repository_satisfies_domain_port_protocol() -> None:
    """Verifies that SQLiteDecisionTraceRepository structurally satisfies DecisionTraceRepository protocol."""
    repo = SQLiteDecisionTraceRepository(db_path="data/test.db")
    assert hasattr(repo, "save")
    assert callable(getattr(repo, "save"))



def test_sqlite_repository_raises_runtime_error_on_db_failure(tmp_path: Path) -> None:
    """Verifies that database operational failure raises RuntimeError."""
    db_file = tmp_path / "invalid_db"
    # Create directory with db name to trigger sqlite operational error on connect/write
    db_file.mkdir()

    repo = SQLiteDecisionTraceRepository(db_path=str(db_file))
    trace = DecisionTrace()
    trace.add_step(name="retrieve")

    with pytest.raises(RuntimeError, match="Failed to initialize SQLite schema|Failed to persist DecisionTrace"):
        repo.save(trace)
