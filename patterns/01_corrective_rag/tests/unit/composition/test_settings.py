"""Unit tests for ApplicationSettings and env loading with fail-fast semantics."""

import pytest

from corrective_rag.composition.settings import (
    DEFAULT_CHROMA_COLLECTION,
    DEFAULT_CHROMA_PATH,
    DEFAULT_RETRIEVER_TOP_K,
    DEFAULT_TRACE_DB_PATH,
    ApplicationSettings,
    load_application_settings_from_env,
)


def test_default_application_settings() -> None:
    """Verifies default values for ApplicationSettings constructor."""
    settings = ApplicationSettings()
    assert settings.chroma_path == DEFAULT_CHROMA_PATH
    assert settings.chroma_collection == DEFAULT_CHROMA_COLLECTION
    assert settings.retriever_top_k == DEFAULT_RETRIEVER_TOP_K
    assert settings.trace_db_path == DEFAULT_TRACE_DB_PATH


def test_load_application_settings_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies loading settings from environment when environment variables are completely unset."""
    monkeypatch.delenv("CRAG_CHROMA_PATH", raising=False)
    monkeypatch.delenv("CRAG_CHROMA_COLLECTION", raising=False)
    monkeypatch.delenv("CRAG_RETRIEVER_TOP_K", raising=False)
    monkeypatch.delenv("CRAG_TRACE_DB_PATH", raising=False)

    settings = load_application_settings_from_env()
    assert settings.chroma_path == "data/chroma"
    assert settings.chroma_collection == "corrective-rag-kb"
    assert settings.retriever_top_k == 4
    assert settings.trace_db_path == "data/traces/crag-traces.db"


def test_load_application_settings_from_env_overrides_with_trimming(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies environment variable overrides for composition settings with surrounding whitespace trimmed."""
    monkeypatch.setenv("CRAG_CHROMA_PATH", " /custom/chroma/path ")
    monkeypatch.setenv("CRAG_CHROMA_COLLECTION", " custom-collection ")
    monkeypatch.setenv("CRAG_RETRIEVER_TOP_K", " 10 ")
    monkeypatch.setenv("CRAG_TRACE_DB_PATH", " /custom/traces/custom-traces.db ")

    settings = load_application_settings_from_env()
    assert settings.chroma_path == "/custom/chroma/path"
    assert settings.chroma_collection == "custom-collection"
    assert settings.retriever_top_k == 10
    assert settings.trace_db_path == "/custom/traces/custom-traces.db"


@pytest.mark.parametrize("blank_val", ["", " ", "   ", "\t"])
def test_load_application_settings_blank_trace_db_path_raises(
    monkeypatch: pytest.MonkeyPatch, blank_val: str
) -> None:
    """Verifies ValueError raised when CRAG_TRACE_DB_PATH is explicitly blank or whitespace-only."""
    monkeypatch.setenv("CRAG_TRACE_DB_PATH", blank_val)
    with pytest.raises(ValueError, match="CRAG_TRACE_DB_PATH cannot be blank"):
        load_application_settings_from_env()


@pytest.mark.parametrize("blank_path", ["", "   "])
def test_application_settings_blank_trace_db_path_raises(blank_path: str) -> None:
    """Verifies ValueError raised when ApplicationSettings(trace_db_path=...) is blank."""
    with pytest.raises(ValueError, match="trace_db_path cannot be empty"):
        ApplicationSettings(trace_db_path=blank_path)



@pytest.mark.parametrize("blank_val", ["", " ", "   ", "\t"])
def test_load_application_settings_blank_chroma_path_raises(
    monkeypatch: pytest.MonkeyPatch, blank_val: str
) -> None:
    """Verifies ValueError raised when CRAG_CHROMA_PATH is explicitly blank or whitespace-only."""
    monkeypatch.setenv("CRAG_CHROMA_PATH", blank_val)
    with pytest.raises(ValueError, match="CRAG_CHROMA_PATH cannot be blank"):
        load_application_settings_from_env()


@pytest.mark.parametrize("blank_val", ["", " ", "   ", "\t"])
def test_load_application_settings_blank_chroma_collection_raises(
    monkeypatch: pytest.MonkeyPatch, blank_val: str
) -> None:
    """Verifies ValueError raised when CRAG_CHROMA_COLLECTION is explicitly blank or whitespace-only."""
    monkeypatch.setenv("CRAG_CHROMA_COLLECTION", blank_val)
    with pytest.raises(ValueError, match="CRAG_CHROMA_COLLECTION cannot be blank"):
        load_application_settings_from_env()


@pytest.mark.parametrize("blank_val", ["", " ", "   ", "\t"])
def test_load_application_settings_blank_retriever_top_k_raises(
    monkeypatch: pytest.MonkeyPatch, blank_val: str
) -> None:
    """Verifies ValueError raised when CRAG_RETRIEVER_TOP_K is explicitly blank or whitespace-only."""
    monkeypatch.setenv("CRAG_RETRIEVER_TOP_K", blank_val)
    with pytest.raises(ValueError, match="CRAG_RETRIEVER_TOP_K cannot be blank"):
        load_application_settings_from_env()


@pytest.mark.parametrize("invalid_env_val", ["abc", "0", "-2"])
def test_load_application_settings_invalid_top_k_env_raises(
    monkeypatch: pytest.MonkeyPatch, invalid_env_val: str
) -> None:
    """Verifies ValueError raised when CRAG_RETRIEVER_TOP_K is non-integer, zero, or negative."""
    monkeypatch.setenv("CRAG_RETRIEVER_TOP_K", invalid_env_val)
    with pytest.raises(ValueError):
        load_application_settings_from_env()


@pytest.mark.parametrize("invalid_top_k", [0, -1, -5])
def test_application_settings_invalid_top_k_raises(invalid_top_k: int) -> None:
    """Verifies ValueError raised when ApplicationSettings(retriever_top_k=...) is <= 0."""
    with pytest.raises(ValueError, match="retriever_top_k must be > 0"):
        ApplicationSettings(retriever_top_k=invalid_top_k)


@pytest.mark.parametrize("blank_path", ["", "   "])
def test_application_settings_blank_path_raises(blank_path: str) -> None:
    """Verifies ValueError raised when ApplicationSettings(chroma_path=...) is blank."""
    with pytest.raises(ValueError, match="chroma_path cannot be empty"):
        ApplicationSettings(chroma_path=blank_path)


@pytest.mark.parametrize("blank_collection", ["", "   "])
def test_application_settings_blank_collection_raises(blank_collection: str) -> None:
    """Verifies ValueError raised when ApplicationSettings(chroma_collection=...) is blank."""
    with pytest.raises(ValueError, match="chroma_collection cannot be empty"):
        ApplicationSettings(chroma_collection=blank_collection)
