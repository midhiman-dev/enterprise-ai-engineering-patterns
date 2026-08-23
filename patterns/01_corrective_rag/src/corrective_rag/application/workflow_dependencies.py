"""Workflow Dependencies container.

Provides explicit dependency injection of Domain ports required by Application node handlers.
"""

from dataclasses import dataclass

from corrective_rag.domain.ports.generator import Generator
from corrective_rag.domain.ports.hallucination_checker import HallucinationChecker
from corrective_rag.domain.ports.query_rewriter import QueryRewriter
from corrective_rag.domain.ports.relevance_grader import RelevanceGrader
from corrective_rag.domain.ports.retriever import Retriever
from corrective_rag.domain.ports.web_search_provider import WebSearchProvider


@dataclass(frozen=True)
class WorkflowDependencies:
    """Container holding domain ports required by the Corrective RAG workflow.

    Dependencies are injected explicitly into node factory functions during graph construction.
    """

    retriever: Retriever
    relevance_grader: RelevanceGrader
    query_rewriter: QueryRewriter
    generator: Generator
    web_search_provider: WebSearchProvider
    hallucination_checker: HallucinationChecker
