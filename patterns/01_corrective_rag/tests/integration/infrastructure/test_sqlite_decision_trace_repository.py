"""Integration tests for SQLiteDecisionTraceRepository persistence adapter."""

from datetime import datetime
from pathlib import Path
import sqlite3

import pytest

from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.infrastructure.persistence.sqlite_decision_trace_repository import (
    SQLiteDecisionTraceRepository,
)


def test_sqlite_schema_initialization(tmp_path: Path) -> None:
    """Verifies that repository idempotently creates required SQLite tables and parent directories."""
    db_path = tmp_path / "nested" / "traces" / "test.db"
    repo = SQLiteDecisionTraceRepository(db_path=str(db_path))

    repo.init_db()

    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "decision_traces" in tables
    assert "decision_trace_steps" in tables


def test_sqlite_trace_persistence_and_ordering(tmp_path: Path) -> None:
    """Verifies that an ordered sequence of TraceSteps is persisted and read back in exact sequence."""
    db_path = tmp_path / "test.db"
    repo = SQLiteDecisionTraceRepository(db_path=str(db_path))

    trace = DecisionTrace()
    trace.add_step(name="retrieve", detail="Top-K: 4")
    trace.add_step(name="grade_documents", detail="Relevant: 2, Irrelevant: 1")
    trace.add_step(name="generate", detail="Model: Groq llama-3.3-70b")
    trace.add_step(name="hallucination_check", detail="Supported: True")

    repo.save(trace)

    persisted_steps = repo.fetch_latest_trace_steps()
    assert len(persisted_steps) == 4
    assert [s.name for s in persisted_steps] == [
        "retrieve",
        "grade_documents",
        "generate",
        "hallucination_check",
    ]
    assert [s.detail for s in persisted_steps] == [
        "Top-K: 4",
        "Relevant: 2, Irrelevant: 1",
        "Model: Groq llama-3.3-70b",
        "Supported: True",
    ]


def test_sqlite_multiple_traces_isolation(tmp_path: Path) -> None:
    """Verifies that multiple traces are stored independently without mixing steps."""
    db_path = tmp_path / "multi_test.db"
    repo = SQLiteDecisionTraceRepository(db_path=str(db_path))

    trace1 = DecisionTrace()
    trace1.add_step(name="retrieve")
    trace1.add_step(name="grade_documents")
    repo.save(trace1)

    trace2 = DecisionTrace()
    trace2.add_step(name="retrieve")
    trace2.add_step(name="rewrite_query")
    trace2.add_step(name="web_search")
    trace2.add_step(name="generate")
    repo.save(trace2)

    t1_steps = repo.fetch_trace_steps_by_id(trace_id=1)
    t2_steps = repo.fetch_trace_steps_by_id(trace_id=2)

    assert [s.name for s in t1_steps] == ["retrieve", "grade_documents"]
    assert [s.name for s in t2_steps] == ["retrieve", "rewrite_query", "web_search", "generate"]


def test_sqlite_reopen_existing_database(tmp_path: Path) -> None:
    """Verifies that repository can reopen and persist to an existing database."""
    db_path = tmp_path / "existing.db"
    repo1 = SQLiteDecisionTraceRepository(db_path=str(db_path))

    trace1 = DecisionTrace()
    trace1.add_step(name="step_in_session_1")
    repo1.save(trace1)

    repo2 = SQLiteDecisionTraceRepository(db_path=str(db_path))
    trace2 = DecisionTrace()
    trace2.add_step(name="step_in_session_2")
    repo2.save(trace2)

    latest_steps = repo2.fetch_latest_trace_steps()
    assert len(latest_steps) == 1
    assert latest_steps[0].name == "step_in_session_2"


def test_sqlite_special_character_escaping(tmp_path: Path) -> None:
    """Verifies that special characters, SQL quotes, newlines, and JSON string details persist accurately."""
    db_path = tmp_path / "escaping.db"
    repo = SQLiteDecisionTraceRepository(db_path=str(db_path))

    special_detail = """{"query": "O'Connor's & 'DROP TABLE decision_traces;--", "unicode": "日本語, 🚀"}"""
    trace = DecisionTrace()
    trace.add_step(name="special_step", detail=special_detail)

    repo.save(trace)

    steps = repo.fetch_latest_trace_steps()
    assert len(steps) == 1
    assert steps[0].name == "special_step"
    assert steps[0].detail == special_detail
