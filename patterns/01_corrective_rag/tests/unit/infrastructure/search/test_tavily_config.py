"""Unit tests for Tavily infrastructure configuration and loader."""

import os
from unittest.mock import patch

import pytest

from corrective_rag.infrastructure.search.tavily_config import (
    DEFAULT_TAVILY_ALLOWED_SOURCE_PREFIXES,
    DEFAULT_TAVILY_MAX_RESULTS,
    TavilyConfig,
    load_tavily_config_from_env,
)


def test_tavily_config_valid() -> None:
    """Verifies TavilyConfig creation with valid parameters."""
    config = TavilyConfig(api_key="tvly-test-key-123", max_results=10)
    assert config.api_key == "tvly-test-key-123"
    assert config.max_results == 10
    assert config.allowed_source_prefixes == DEFAULT_TAVILY_ALLOWED_SOURCE_PREFIXES


def test_tavily_config_accepts_custom_authoritative_prefixes() -> None:
    config = TavilyConfig(
        api_key="tvly-test-key",
        allowed_source_prefixes=("https://docs.example.com/",),
    )
    assert config.allowed_source_prefixes == ("https://docs.example.com/",)


def test_tavily_config_missing_api_key_raises() -> None:
    """Verifies TavilyConfig raises ValueError for empty API key."""
    with pytest.raises(ValueError, match="TAVILY_API_KEY is required"):
        TavilyConfig(api_key="")


def test_tavily_config_blank_api_key_raises() -> None:
    """Verifies TavilyConfig raises ValueError for whitespace API key."""
    with pytest.raises(ValueError, match="TAVILY_API_KEY is required"):
        TavilyConfig(api_key="   \t\n  ")


@pytest.mark.parametrize("invalid_max_results", [0, -1, -5])
def test_tavily_config_invalid_max_results_raises(invalid_max_results: int) -> None:
    """Verifies TavilyConfig raises ValueError when max_results <= 0."""
    with pytest.raises(ValueError, match="max_results must be greater than 0"):
        TavilyConfig(api_key="tvly-test-key", max_results=invalid_max_results)


def test_tavily_config_rejects_empty_source_allowlist() -> None:
    with pytest.raises(ValueError, match="allowed_source_prefixes must contain at least one source"):
        TavilyConfig(api_key="tvly-test-key", allowed_source_prefixes=())


@pytest.mark.parametrize(
    "invalid_prefix",
    ["http://kubernetes.io/", "kubernetes.io/docs", "   "],
)
def test_tavily_config_rejects_non_https_or_invalid_source_prefix(invalid_prefix: str) -> None:
    with pytest.raises(ValueError):
        TavilyConfig(
            api_key="tvly-test-key",
            allowed_source_prefixes=(invalid_prefix,),
        )


def test_load_tavily_config_from_env_valid() -> None:
    """Verifies loading TavilyConfig from valid environment variables."""
    with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-env-key-456"}, clear=True):
        config = load_tavily_config_from_env()
        assert config.api_key == "tvly-env-key-456"
        assert config.max_results == DEFAULT_TAVILY_MAX_RESULTS
        assert config.allowed_source_prefixes == DEFAULT_TAVILY_ALLOWED_SOURCE_PREFIXES


def test_load_tavily_config_from_env_override_max_results() -> None:
    """Verifies TAVILY_MAX_RESULTS environment variable override."""
    with patch.dict(
        os.environ,
        {"TAVILY_API_KEY": "tvly-env-key", "TAVILY_MAX_RESULTS": "3"},
        clear=True,
    ):
        config = load_tavily_config_from_env()
        assert config.max_results == 3


def test_load_tavily_config_from_env_override_allowed_source_prefixes() -> None:
    with patch.dict(
        os.environ,
        {
            "TAVILY_API_KEY": "tvly-env-key",
            "TAVILY_ALLOWED_SOURCE_PREFIXES": (
                "https://docs.example.com/, https://security.example.com/kb/"
            ),
        },
        clear=True,
    ):
        config = load_tavily_config_from_env()
        assert config.allowed_source_prefixes == (
            "https://docs.example.com/",
            "https://security.example.com/kb/",
        )


def test_load_tavily_config_from_env_missing_key_raises() -> None:
    """Verifies load_tavily_config_from_env raises ValueError when TAVILY_API_KEY is absent."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError, match="TAVILY_API_KEY is required"):
            load_tavily_config_from_env()


@pytest.mark.parametrize("invalid_val", ["abc", "0", "-2"])
def test_load_tavily_config_from_env_invalid_max_results_raises(invalid_val: str) -> None:
    """Verifies load_tavily_config_from_env raises ValueError for invalid max_results string."""
    with patch.dict(
        os.environ,
        {"TAVILY_API_KEY": "tvly-env-key", "TAVILY_MAX_RESULTS": invalid_val},
        clear=True,
    ):
        with pytest.raises(ValueError):
            load_tavily_config_from_env()


def test_load_tavily_config_from_env_blank_source_prefixes_raises() -> None:
    with patch.dict(
        os.environ,
        {
            "TAVILY_API_KEY": "tvly-env-key",
            "TAVILY_ALLOWED_SOURCE_PREFIXES": " ,  , ",
        },
        clear=True,
    ):
        with pytest.raises(ValueError, match="must contain at least one HTTPS source prefix"):
            load_tavily_config_from_env()
