"""Tavily Web Search Infrastructure Configuration.

Provides configuration data model and environment variable loader for the Tavily
web search adapter.
"""

from dataclasses import dataclass
import os

DEFAULT_TAVILY_MAX_RESULTS = 5


@dataclass(frozen=True)
class TavilyConfig:
    """Infrastructure configuration for Tavily web search provider.

    Attributes:
        api_key: Secret API key for Tavily search API authentication.
        max_results: Maximum number of search results to retrieve (must be > 0).
    """

    api_key: str
    max_results: int = DEFAULT_TAVILY_MAX_RESULTS

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("TAVILY_API_KEY is required.")
        if self.max_results <= 0:
            raise ValueError("max_results must be greater than 0.")


def load_tavily_config_from_env() -> TavilyConfig:
    """Loads TavilyConfig from standard environment variables.

    Environment variables inspected:
        TAVILY_API_KEY: Required authentication key.
        TAVILY_MAX_RESULTS: Optional result count limit override.

    Returns:
        Validated TavilyConfig instance.

    Raises:
        ValueError: If TAVILY_API_KEY is missing/blank or TAVILY_MAX_RESULTS is invalid.
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
            raise ValueError(f"Invalid TAVILY_MAX_RESULTS: '{raw_max_results}'. Must be a positive integer.") from exc

        if parsed_max_results <= 0:
            raise ValueError("max_results must be greater than 0.")
        max_results = parsed_max_results

    return TavilyConfig(
        api_key=api_key,
        max_results=max_results,
    )
