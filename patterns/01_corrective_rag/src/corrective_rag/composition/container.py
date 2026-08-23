"""Composition Root Container and Application Assembly.

Assembles concrete Infrastructure adapters, constructs WorkflowDependencies,
and compiles the LangGraph StateGraph application.
"""

from typing import Any

import chromadb
from langgraph.graph.state import CompiledStateGraph

from corrective_rag.application.workflow import build_graph
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.composition.settings import (
    ApplicationSettings,
    load_application_settings_from_env,
)
from corrective_rag.infrastructure.embeddings.local_embedding import DefaultLocalEmbeddingFunction
from corrective_rag.infrastructure.generation.groq_client import (
    GroqChatClient,
    GroqSdkChatClient,
)
from corrective_rag.infrastructure.generation.groq_config import (
    GroqConfig,
    load_groq_config_from_env,
)
from corrective_rag.infrastructure.generation.groq_generator import GroqGenerator
from corrective_rag.infrastructure.grading.groq_relevance_grader import GroqRelevanceGrader
from corrective_rag.infrastructure.retrieval.chroma_retriever import ChromaRetriever
from corrective_rag.infrastructure.search.groq_query_rewriter import GroqQueryRewriter
from corrective_rag.infrastructure.search.tavily_client import (
    TavilySdkSearchClient,
    TavilySearchClient,
)
from corrective_rag.infrastructure.search.tavily_config import (
    TavilyConfig,
    load_tavily_config_from_env,
)
from corrective_rag.infrastructure.search.tavily_web_search_provider import TavilyWebSearchProvider
from corrective_rag.infrastructure.verification.groq_hallucination_checker import (
    GroqHallucinationChecker,
)


def build_dependencies(
    settings: ApplicationSettings | None = None,
    groq_config: GroqConfig | None = None,
    tavily_config: TavilyConfig | None = None,
    groq_client: GroqChatClient | None = None,
    tavily_client: TavilySearchClient | None = None,
    chroma_collection: Any | None = None,
) -> WorkflowDependencies:
    """Constructs concrete Infrastructure capability adapters and injects them into WorkflowDependencies.

    Args:
        settings: Optional composition settings. If None, loaded from env.
        groq_config: Optional Groq configuration override. If None, loaded from env.
        tavily_config: Optional Tavily configuration override. If None, loaded from env.
        groq_client: Optional GroqChatClient override for shared low-level SDK client.
        tavily_client: Optional TavilySearchClient override for search SDK client.
        chroma_collection: Optional Chroma collection instance override.

    Returns:
        Fully wired WorkflowDependencies container.

    Raises:
        ValueError: If required environment configurations are missing or invalid.
    """
    settings = settings or load_application_settings_from_env()
    groq_config = groq_config or load_groq_config_from_env()
    tavily_config = tavily_config or load_tavily_config_from_env()

    if groq_client is None:
        groq_client = GroqSdkChatClient(api_key=groq_config.api_key)

    if tavily_client is None:
        tavily_client = TavilySdkSearchClient(api_key=tavily_config.api_key)

    if chroma_collection is None:
        embedding_fn = DefaultLocalEmbeddingFunction()
        chroma_client = chromadb.PersistentClient(path=settings.chroma_path)
        chroma_collection = chroma_client.get_or_create_collection(
            name=settings.chroma_collection,
            embedding_function=embedding_fn,
        )

    retriever = ChromaRetriever(
        collection=chroma_collection,
        top_k=settings.retriever_top_k,
    )
    relevance_grader = GroqRelevanceGrader(
        config=groq_config,
        client=groq_client,
    )
    query_rewriter = GroqQueryRewriter(
        config=groq_config,
        client=groq_client,
    )
    generator = GroqGenerator(
        config=groq_config,
        client=groq_client,
    )
    web_search_provider = TavilyWebSearchProvider(
        config=tavily_config,
        client=tavily_client,
    )
    hallucination_checker = GroqHallucinationChecker(
        config=groq_config,
        client=groq_client,
    )

    return WorkflowDependencies(
        retriever=retriever,
        relevance_grader=relevance_grader,
        query_rewriter=query_rewriter,
        generator=generator,
        web_search_provider=web_search_provider,
        hallucination_checker=hallucination_checker,
    )


def build_application(
    settings: ApplicationSettings | None = None,
    dependencies: WorkflowDependencies | None = None,
    groq_config: GroqConfig | None = None,
    tavily_config: TavilyConfig | None = None,
    groq_client: GroqChatClient | None = None,
    tavily_client: TavilySearchClient | None = None,
    chroma_collection: Any | None = None,
) -> CompiledStateGraph:
    """Builds and compiles the Corrective RAG LangGraph workflow.

    Args:
        settings: Optional composition settings.
        dependencies: Optional pre-constructed WorkflowDependencies container.
        groq_config: Optional Groq configuration override.
        tavily_config: Optional Tavily configuration override.
        groq_client: Optional Groq client override.
        tavily_client: Optional Tavily client override.
        chroma_collection: Optional Chroma collection override.

    Returns:
        CompiledStateGraph application ready for state execution.
    """
    if dependencies is None:
        dependencies = build_dependencies(
            settings=settings,
            groq_config=groq_config,
            tavily_config=tavily_config,
            groq_client=groq_client,
            tavily_client=tavily_client,
            chroma_collection=chroma_collection,
        )

    return build_graph(dependencies)
