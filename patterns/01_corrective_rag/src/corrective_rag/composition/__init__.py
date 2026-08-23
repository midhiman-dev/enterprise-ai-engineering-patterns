"""Composition Root package.

Wires concrete Infrastructure adapters to Application use cases and constructs the application graph.
Acts as the single place where dependency injection is assembled.
"""

from corrective_rag.composition.container import build_application, build_dependencies
from corrective_rag.composition.environment import load_local_environment
from corrective_rag.composition.settings import (
    ApplicationSettings,
    load_application_settings_from_env,
)

__all__ = [
    "ApplicationSettings",
    "build_application",
    "build_dependencies",
    "load_application_settings_from_env",
    "load_local_environment",
]
