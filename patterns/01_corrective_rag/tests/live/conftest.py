"""Pytest conftest fixture for live integration tests.

Automatically loads developer-local `.env` variables before running live tests.
"""

import pytest

from corrective_rag.composition.environment import load_local_environment


@pytest.fixture(scope="session", autouse=True)
def load_live_environment() -> None:
    """Automatically loads developer-local `.env` file into process environment for live tests."""
    load_local_environment()
