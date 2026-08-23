"""Unit tests for developer-local environment bootstrap (load_local_environment)."""

import os
from pathlib import Path
import pytest

from corrective_rag.composition.environment import load_local_environment


def test_load_local_environment_missing_file(tmp_path: Path) -> None:
    """Verifies that a non-existent `.env` file is handled gracefully without raising an exception."""
    missing_file = tmp_path / "non_existent.env"
    load_local_environment(dotenv_path=missing_file)


def test_load_local_environment_loads_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies that values in `.env` are loaded into `os.environ` when variables are absent."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("CRAG_RETRIEVER_TOP_K", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=test-groq-key-123\n"
        "TAVILY_API_KEY=test-tavily-key-456\n"
        "CRAG_RETRIEVER_TOP_K=8\n",
        encoding="utf-8",
    )

    load_local_environment(dotenv_path=env_file)

    assert os.getenv("GROQ_API_KEY") == "test-groq-key-123"
    assert os.getenv("TAVILY_API_KEY") == "test-tavily-key-456"
    assert os.getenv("CRAG_RETRIEVER_TOP_K") == "8"


def test_load_local_environment_existing_env_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies process/host environment variables win over `.env` values (override=False)."""
    monkeypatch.setenv("GROQ_API_KEY", "host-groq-key")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=file-groq-key\n"
        "TAVILY_API_KEY=file-tavily-key\n",
        encoding="utf-8",
    )

    load_local_environment(dotenv_path=env_file)

    assert os.getenv("GROQ_API_KEY") == "host-groq-key"
    assert os.getenv("TAVILY_API_KEY") == "file-tavily-key"


def test_load_local_environment_default_path() -> None:
    """Verifies calling `load_local_environment()` without arguments runs cleanly."""
    load_local_environment()
