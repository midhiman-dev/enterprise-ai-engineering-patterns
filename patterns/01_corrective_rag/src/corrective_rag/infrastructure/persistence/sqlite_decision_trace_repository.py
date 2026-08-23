"""SQLite DecisionTrace Repository Infrastructure Adapter.

Implements persistent storage for the CRAG workflow's DecisionTrace audit records using
Python's standard-library sqlite3.
"""

from datetime import datetime
import os
import sqlite3

from corrective_rag.domain.entities.decision_trace import DecisionTrace, TraceStep

DEFAULT_TRACE_DB_PATH = "data/traces/crag-traces.db"


class SQLiteDecisionTraceRepository:

    """Infrastructure implementation of DecisionTraceRepository using SQLite.

    Does NOT inherit from the DecisionTraceRepository Protocol (structural subtyping).
    Uses standard-library sqlite3 for zero-infrastructure local persistence.
    """

    def __init__(self, db_path: str = DEFAULT_TRACE_DB_PATH) -> None:
        """Initializes the repository with a target SQLite database path.

        Args:
            db_path: File path for the SQLite database.

        Raises:
            ValueError: If db_path is empty or whitespace-only.
        """
        if not db_path or not db_path.strip():
            raise ValueError("db_path cannot be empty or whitespace-only.")
        self._db_path = db_path.strip()

    @property
    def db_path(self) -> str:
        """Returns the configured database file path."""
        return self._db_path

    def init_db(self) -> None:
        """Idempotently initializes the database schema and parent directory.

        Creates target parent directories if absent.
        Executes CREATE TABLE IF NOT EXISTS statements for decision_traces and decision_trace_steps.

        Raises:
            RuntimeError: If schema creation fails due to a database operational error.
        """
        dir_path = os.path.dirname(self._db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS decision_traces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS decision_trace_steps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trace_id INTEGER NOT NULL,
                        sequence_number INTEGER NOT NULL,
                        step_name TEXT NOT NULL,
                        detail TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (trace_id) REFERENCES decision_traces(id) ON DELETE CASCADE
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_trace_steps_trace_id
                    ON decision_trace_steps(trace_id)
                    """
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to initialize SQLite schema at {self._db_path}: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()

    def save(self, trace: DecisionTrace) -> None:
        """Persists a DecisionTrace entity and its ordered steps atomically into SQLite.

        Satisfies the DecisionTraceRepository Domain port contract.

        Args:
            trace: The DecisionTrace domain entity to save.

        Raises:
            RuntimeError: If database connection or insertion fails.
        """
        self.init_db()
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            with conn:
                cursor = conn.cursor()
                now_iso = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO decision_traces (created_at) VALUES (?)",
                    (now_iso,),
                )
                trace_id = cursor.lastrowid
                for idx, step in enumerate(trace.steps):
                    cursor.execute(
                        """
                        INSERT INTO decision_trace_steps
                        (trace_id, sequence_number, step_name, detail, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            trace_id,
                            idx,
                            step.name,
                            step.detail,
                            step.timestamp.isoformat(),
                        ),
                    )
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to persist DecisionTrace to SQLite: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()

    def fetch_latest_trace_steps(self) -> tuple[TraceStep, ...]:
        """Infrastructure readback helper: retrieves ordered steps for the most recently saved trace.

        Returns:
            Tuple of TraceStep objects in exact execution order.

        Raises:
            RuntimeError: If query execution fails or database is missing.
        """
        self.init_db()
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM decision_traces")
            row = cursor.fetchone()
            if not row or row[0] is None:
                return ()
            latest_id = row[0]
            return self.fetch_trace_steps_by_id(latest_id)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to fetch latest trace steps from SQLite: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()

    def fetch_trace_steps_by_id(self, trace_id: int) -> tuple[TraceStep, ...]:
        """Infrastructure readback helper: retrieves ordered steps for a specific trace_id.

        Args:
            trace_id: Integer primary key of the target trace record.

        Returns:
            Tuple of TraceStep objects in explicit sequence_number order.

        Raises:
            RuntimeError: If query execution fails.
        """
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT step_name, detail, timestamp
                FROM decision_trace_steps
                WHERE trace_id = ?
                ORDER BY sequence_number ASC
                """,
                (trace_id,),
            )
            rows = cursor.fetchall()
            steps = []
            for name, detail, ts_str in rows:
                timestamp = datetime.fromisoformat(ts_str)
                steps.append(TraceStep(name=name, detail=detail, timestamp=timestamp))
            return tuple(steps)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to fetch trace steps for trace_id {trace_id}: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()

