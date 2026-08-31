"""Unit tests for Composition Root dependency wiring and application assembly."""

import pathlib
from unittest.mock import MagicMock

import chromadb
from langgraph.graph.state import CompiledStateGraph
import pytest

from corrective_rag.application.application import CorrectiveRAGApplication
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.composition.container import build_application, build_dependencies
from corrective_rag.composition.settings import ApplicationSettings
from corrective_rag.infrastructure.generation.groq_client import GroqChatClient
from corrective_rag.infrastructure.generation.groq_config import GroqConfig
from corrective_rag.infrastructure.generation.groq_generator import GroqGenerator
from corrective_rag.infrastructure.grading.groq_relevance_grader import GroqRelevanceGrader
from corrective_rag.infrastructure.persistence.sqlite_decision_trace_repository import (
    SQLiteDecisionTraceRepository,
)
from corrective_rag.infrastructure.retrieval.chroma_retriever import ChromaRetriever
from corrective_rag.infrastructure.search.groq_query_rewriter import GroqQueryRewriter
from corrective_rag.infrastructure.search.tavily_client import TavilySearchClient
from corrective_rag.infrastructure.search.tavily_config import TavilyConfig
from corrective_rag.infrastructure.search.tavily_web_search_provider import TavilyWebSearchProvider
from corrective_rag.infrastructure.verification.groq_hallucination_checker import (
    GroqHallucinationChecker,
)
from tests.unit.application.fakes import FakeDecisionTraceRepository


@pytest.fixture
def mock_groq_config() -> GroqConfig:
    """Fixture supplying valid GroqConfig."""
    return GroqConfig(api_key="test-groq-key")


@pytest.fixture
def mock_tavily_config() -> TavilyConfig:
    """Fixture supplying valid TavilyConfig."""
    return TavilyConfig(api_key="test-tavily-key")


@pytest.fixture
def mock_groq_client() -> GroqChatClient:
    """Fixture supplying mock Groq client interface."""
    return MagicMock(spec=GroqChatClient)


@pytest.fixture
def mock_tavily_client() -> TavilySearchClient:
    """Fixture supplying mock Tavily client interface."""
    return MagicMock(spec=TavilySearchClient)


@pytest.fixture
def mock_chroma_collection() -> chromadb.Collection:
    """Fixture supplying mock Chroma collection."""
    return MagicMock(spec=chromadb.Collection)


def test_build_dependencies_selects_real_adapters(
    mock_groq_config: GroqConfig,
    mock_tavily_config: TavilyConfig,
    mock_groq_client: GroqChatClient,
    mock_tavily_client: TavilySearchClient,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies build_dependencies instantiates all six graph concrete Infrastructure capability adapters."""
    settings = ApplicationSettings(retriever_top_k=5)

    deps = build_dependencies(
        settings=settings,
        groq_config=mock_groq_config,
        tavily_config=mock_tavily_config,
        groq_client=mock_groq_client,
        tavily_client=mock_tavily_client,
        chroma_collection=mock_chroma_collection,
    )

    assert isinstance(deps, WorkflowDependencies)
    assert isinstance(deps.retriever, ChromaRetriever)
    assert isinstance(deps.relevance_grader, GroqRelevanceGrader)
    assert isinstance(deps.query_rewriter, GroqQueryRewriter)
    assert isinstance(deps.generator, GroqGenerator)
    assert isinstance(deps.web_search_provider, TavilyWebSearchProvider)
    assert isinstance(deps.hallucination_checker, GroqHallucinationChecker)
    assert not hasattr(deps, "decision_trace_repository")


def test_groq_adapters_share_single_client_instance(
    mock_groq_config: GroqConfig,
    mock_tavily_config: TavilyConfig,
    mock_groq_client: GroqChatClient,
    mock_tavily_client: TavilySearchClient,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies that all four Groq-backed adapters share the exact same low-level GroqChatClient instance."""
    deps = build_dependencies(
        groq_config=mock_groq_config,
        tavily_config=mock_tavily_config,
        groq_client=mock_groq_client,
        tavily_client=mock_tavily_client,
        chroma_collection=mock_chroma_collection,
    )

    # Inspect internal client attributes of the constructed Groq adapters
    assert deps.relevance_grader._client is mock_groq_client  # type: ignore[attr-defined]
    assert deps.query_rewriter._client is mock_groq_client  # type: ignore[attr-defined]
    assert deps.generator._client is mock_groq_client  # type: ignore[attr-defined]
    assert deps.hallucination_checker._client is mock_groq_client  # type: ignore[attr-defined]


def test_workflow_dependencies_is_fully_populated(
    mock_groq_config: GroqConfig,
    mock_tavily_config: TavilyConfig,
    mock_groq_client: GroqChatClient,
    mock_tavily_client: TavilySearchClient,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies every field in WorkflowDependencies is populated and non-None."""
    deps = build_dependencies(
        groq_config=mock_groq_config,
        tavily_config=mock_tavily_config,
        groq_client=mock_groq_client,
        tavily_client=mock_tavily_client,
        chroma_collection=mock_chroma_collection,
    )

    assert deps.retriever is not None
    assert deps.relevance_grader is not None
    assert deps.query_rewriter is not None
    assert deps.generator is not None
    assert deps.web_search_provider is not None
    assert deps.hallucination_checker is not None


def test_build_application_produces_application_bundle_with_override(
    mock_groq_config: GroqConfig,
    mock_tavily_config: TavilyConfig,
    mock_groq_client: GroqChatClient,
    mock_tavily_client: TavilySearchClient,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies build_application returns a CorrectiveRAGApplication bundling graph and custom repository override."""
    fake_repo = FakeDecisionTraceRepository()
    app = build_application(
        groq_config=mock_groq_config,
        tavily_config=mock_tavily_config,
        groq_client=mock_groq_client,
        tavily_client=mock_tavily_client,
        chroma_collection=mock_chroma_collection,
        decision_trace_repository=fake_repo,
    )

    assert isinstance(app, CorrectiveRAGApplication)
    assert isinstance(app.graph, CompiledStateGraph)
    assert app.repository is fake_repo


def test_build_application_defaults_to_sqlite_repository(
    mock_groq_config: GroqConfig,
    mock_tavily_config: TavilyConfig,
    mock_groq_client: GroqChatClient,
    mock_tavily_client: TavilySearchClient,
    mock_chroma_collection: chromadb.Collection,
    tmp_path: pathlib.Path,
) -> None:
    """Verifies build_application creates SQLiteDecisionTraceRepository with settings.trace_db_path by default."""
    custom_db_path = str(tmp_path / "custom_trace.db")
    settings = ApplicationSettings(trace_db_path=custom_db_path)

    app = build_application(
        settings=settings,
        groq_config=mock_groq_config,
        tavily_config=mock_tavily_config,
        groq_client=mock_groq_client,
        tavily_client=mock_tavily_client,
        chroma_collection=mock_chroma_collection,
    )

    assert isinstance(app, CorrectiveRAGApplication)
    assert isinstance(app.repository, SQLiteDecisionTraceRepository)
    assert app.repository.db_path == custom_db_path


def test_missing_groq_api_key_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
    mock_tavily_config: TavilyConfig,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies build_dependencies fails fast with ValueError when GROQ_API_KEY is missing."""
    monkeypatch.setattr("corrective_rag.composition.container.load_local_environment", lambda: None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
        build_dependencies(
            tavily_config=mock_tavily_config,
            chroma_collection=mock_chroma_collection,
        )


def test_missing_tavily_api_key_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
    mock_groq_config: GroqConfig,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies build_dependencies fails fast with ValueError when TAVILY_API_KEY is missing."""
    monkeypatch.setattr("corrective_rag.composition.container.load_local_environment", lambda: None)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(ValueError, match="TAVILY_API_KEY is required"):
        build_dependencies(
            groq_config=mock_groq_config,
            chroma_collection=mock_chroma_collection,
        )


def test_invalid_composition_settings_fail_fast(
    mock_groq_config: GroqConfig,
    mock_tavily_config: TavilyConfig,
    mock_groq_client: GroqChatClient,
    mock_tavily_client: TavilySearchClient,
    mock_chroma_collection: chromadb.Collection,
) -> None:
    """Verifies invalid composition settings fail before constructing dependencies."""
    with pytest.raises(ValueError, match="retriever_top_k must be > 0"):
        ApplicationSettings(retriever_top_k=-1)
