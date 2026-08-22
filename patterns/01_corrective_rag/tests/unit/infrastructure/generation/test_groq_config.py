"""Unit tests for GroqConfig and load_groq_config_from_env."""

import pytest

from corrective_rag.infrastructure.generation.groq_config import (
    DEFAULT_GROQ_MODEL,
    GroqConfig,
    load_groq_config_from_env,
)


def test_load_groq_config_from_env_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests loading valid GroqConfig with custom model override."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_secret_key_12345")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")

    config = load_groq_config_from_env()

    assert config.api_key == "gsk_test_secret_key_12345"
    assert config.model == "llama-3.1-8b-instant"
    assert config.temperature == 0.0


def test_load_groq_config_from_env_default_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests loading valid GroqConfig using default model when GROQ_MODEL is unset."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_secret_key_12345")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    config = load_groq_config_from_env()

    assert config.api_key == "gsk_test_secret_key_12345"
    assert config.model == DEFAULT_GROQ_MODEL
    assert config.temperature == 0.0


def test_load_groq_config_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that missing GROQ_API_KEY raises a clear ValueError."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
        load_groq_config_from_env()


def test_load_groq_config_blank_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests that whitespace-only GROQ_API_KEY raises a clear ValueError."""
    monkeypatch.setenv("GROQ_API_KEY", "   ")

    with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
        load_groq_config_from_env()
