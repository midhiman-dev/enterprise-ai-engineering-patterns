"""Unit tests for ApplicationSettings and env loading."""

import pytest

from corrective_rag.composition.settings import (
    DEFAULT_CHROMA_COLLECTION,
    DEFAULT_CHROMA_PATH,
    DEFAULT_RETRIEVER_TOP_K,
    ApplicationSettings,
    load_application_settings_from_env,
)


def test_default_application_settings() -> None:
    """Verifies default values for ApplicationSettings."""
    settings = ApplicationSettings()
    assert settings.chroma_path == DEFAULT_CHROMA_PATH
    assert settings.chroma_collection == DEFAULT_CHROMA_COLLECTION
    assert settings.retriever_top_k == DEFAULT_RETRIEVER_TOP_K


def test_load_application_settings_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies loading settings from environment when environment variables are unset."""
    monkeypatch.delenv("CRAG_CHROMA_PATH", raising=False)
    monkeypatch.delenv("CRAG_CHROMA_COLLECTION", raising=False)
    monkeypatch.delenv("CRAG_RETRIEVER_TOP_K", raising=False)

    settings = load_application_settings_from_env()
    assert settings.chroma_path == "data/chroma"
    assert settings.chroma_collection == "corrective-rag-kb"
    assert settings.retriever_top_k == 4


def test_load_application_settings_from_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies environment variable overrides for composition settings."""
    monkeypatch.setenv("CRAG_CHROMA_PATH", "/custom/chroma/path")
    monkeypatch.setenv("CRAG_CHROMA_COLLECTION", "custom-collection")
    monkeypatch.setenv("CRAG_RETRIEVER_TOP_K", "10")

    settings = load_application_settings_from_env()
    assert settings.chroma_path == "/custom/chroma/path"
    assert settings.chroma_collection == "custom-collection"
    assert settings.retriever_top_k == 10


@pytest.mark.parametrize("invalid_top_k", [0, -1, -5])
def test_application_settings_invalid_top_k_raises(invalid_top_k: int) -> None:
    """Verifies ValueError raised when top_k <= 0."""
    with pytest.raises(ValueError, match="retriever_top_k must be > 0"):
        ApplicationSettings(retriever_top_k=invalid_top_k)


@pytest.mark.parametrize("blank_path", ["", "   "])
def test_application_settings_blank_path_raises(blank_path: str) -> None:
    """Verifies ValueError raised when chroma_path is blank."""
    with pytest.raises(ValueError, match="chroma_path cannot be empty"):
        ApplicationSettings(chroma_path=blank_path)


@pytest.mark.parametrize("blank_collection", ["", "   "])
def test_application_settings_blank_collection_raises(blank_collection: str) -> None:
    """Verifies ValueError raised when chroma_collection is blank."""
    with pytest.raises(ValueError, match="chroma_collection cannot be empty"):
        ApplicationSettings(chroma_collection=blank_collection)


@pytest.mark.parametrize("invalid_env_val", ["abc", "0", "-2"])
def test_load_application_settings_invalid_top_k_env_raises(
    monkeypatch: pytest.MonkeyPatch, invalid_env_val: str
) -> None:
    """Verifies ValueError raised when CRAG_RETRIEVER_TOP_K is non-integer or <= 0."""
    monkeypatch.setenv("CRAG_RETRIEVER_TOP_K", invalid_env_val)
    with pytest.raises(ValueError):
        load_application_settings_from_env()
