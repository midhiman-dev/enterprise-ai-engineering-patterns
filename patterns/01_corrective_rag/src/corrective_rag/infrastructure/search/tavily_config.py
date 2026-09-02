"""Tavily Web Search Infrastructure Configuration.

Provides configuration data model and environment variable loader for the Tavily
web search adapter.

Security boundary:
    Corrective web search introduces untrusted external content into the RAG evidence
    path. The adapter therefore applies a deterministic allowlist before external
    evidence is admitted into the generation context.
"""

from dataclasses import dataclass
import os
from urllib.parse import urlparse

DEFAULT_TAVILY_MAX_RESULTS = 5
DEFAULT_TAVILY_ALLOWED_SOURCE_PREFIXES = (
    "https://kubernetes.io/",
    "https://github.com/kubernetes/",
)


def _validate_source_prefix(prefix: str) -> str:
    """Validate one authoritative HTTPS source prefix and return its stripped value."""
    normalized = prefix.strip()
    if not normalized:
        raise ValueError("allowed source prefixes cannot contain blank values.")

    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(
            "allowed source prefixes must be absolute HTTPS URLs, "
            f"got: '{normalized}'"
        )
    return normalized


@dataclass(frozen=True)
class TavilyConfig:
    """Infrastructure configuration for Tavily web search provider.

    Attributes:
        api_key: Secret API key for Tavily search API authentication.
        max_results: Maximum number of search results to retrieve (must be > 0).
        allowed_source_prefixes: Authoritative HTTPS URL prefixes permitted to cross
            the external-evidence trust boundary.
    """

    api_key: str
    max_results: int = DEFAULT_TAVILY_MAX_RESULTS
    allowed_source_prefixes: tuple[str, ...] = DEFAULT_TAVILY_ALLOWED_SOURCE_PREFIXES

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("TAVILY_API_KEY is required.")
        if self.max_results <= 0:
            raise ValueError("max_results must be greater than 0.")
        if not self.allowed_source_prefixes:
            raise ValueError("allowed_source_prefixes must contain at least one source.")

        normalized_prefixes = tuple(
            _validate_source_prefix(prefix) for prefix in self.allowed_source_prefixes
        )
        object.__setattr__(self, "allowed_source_prefixes", normalized_prefixes)


def load_tavily_config_from_env() -> TavilyConfig:
    """Loads TavilyConfig from standard environment variables.

    Environment variables inspected:
        TAVILY_API_KEY: Required authentication key.
        TAVILY_MAX_RESULTS: Optional result count limit override.
        TAVILY_ALLOWED_SOURCE_PREFIXES: Optional comma-separated authoritative HTTPS
            URL prefixes. Defaults to Kubernetes official documentation and the
            Kubernetes GitHub organization.

    Returns:
        Validated TavilyConfig instance.

    Raises:
        ValueError: If any required or security-sensitive configuration is invalid.
    """
    raw_api_key = os.getenv("TAVILY_API_KEY")
    if not raw_api_key or not raw_api_key.strip():
        raise ValueError("TAVILY_API_KEY is required.")

    api_key = raw_api_key.strip()

    max_results = DEFAULT_TAVILY_MAX_RESULTS
    raw_max_results = os.getenv("TAVILY_MAX_RESULTS")
    if raw_max_results and raw_max_results.strip():
        try:
            parsed_max_results = int(raw_max_results.strip())
        except ValueError as exc:
            raise ValueError(
                f"Invalid TAVILY_MAX_RESULTS: '{raw_max_results}'. Must be a positive integer."
            ) from exc

        if parsed_max_results <= 0:
            raise ValueError("max_results must be greater than 0.")
        max_results = parsed_max_results

    allowed_source_prefixes = DEFAULT_TAVILY_ALLOWED_SOURCE_PREFIXES
    raw_prefixes = os.getenv("TAVILY_ALLOWED_SOURCE_PREFIXES")
    if raw_prefixes is not None:
        parsed_prefixes = tuple(
            item.strip() for item in raw_prefixes.split(",") if item.strip()
        )
        if not parsed_prefixes:
            raise ValueError(
                "TAVILY_ALLOWED_SOURCE_PREFIXES must contain at least one HTTPS source prefix."
            )
        allowed_source_prefixes = parsed_prefixes

    return TavilyConfig(
        api_key=api_key,
        max_results=max_results,
        allowed_source_prefixes=allowed_source_prefixes,
    )
