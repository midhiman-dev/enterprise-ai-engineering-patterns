"""Groq Infrastructure Configuration.

Provides minimal configuration data model and environment variable loader for
the Groq hosted generation adapter.
"""

from dataclasses import dataclass
import os

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


@dataclass(frozen=True)
class GroqConfig:
    """Infrastructure configuration for Groq hosted generation provider.

    Attributes:
        api_key: Secret API key for Groq service authentication.
        model: Target LLM model identifier on Groq platform.
        temperature: Sampling temperature for candidate generation.
    """

    api_key: str
    model: str = DEFAULT_GROQ_MODEL
    temperature: float = 0.0


def load_groq_config_from_env() -> GroqConfig:
    """Loads GroqConfig from standard environment variables.

    Environment variables inspected:
        GROQ_API_KEY: Required authentication key.
        GROQ_MODEL: Optional target model override.

    Returns:
        Validated GroqConfig instance.

    Raises:
        ValueError: If GROQ_API_KEY is missing or blank.
    """
    raw_api_key = os.getenv("GROQ_API_KEY")
    if not raw_api_key or not raw_api_key.strip():
        raise ValueError("GROQ_API_KEY is required.")

    api_key = raw_api_key.strip()

    raw_model = os.getenv("GROQ_MODEL")
    model = raw_model.strip() if raw_model and raw_model.strip() else DEFAULT_GROQ_MODEL

    return GroqConfig(
        api_key=api_key,
        model=model,
        temperature=0.0,
    )
