"""Domain Ports package.

Defines provider-neutral capability contracts (Protocols) required by the
Corrective RAG workflow. Adapters in the Infrastructure layer satisfy these
contracts structurally without inheritance.
"""

from corrective_rag.domain.ports.decision_trace_repository import DecisionTraceRepository
from corrective_rag.domain.ports.generator import Generator
from corrective_rag.domain.ports.hallucination_checker import HallucinationChecker
from corrective_rag.domain.ports.query_rewriter import QueryRewriter
from corrective_rag.domain.ports.relevance_grader import RelevanceGrader
from corrective_rag.domain.ports.retriever import Retriever
from corrective_rag.domain.ports.web_search_provider import WebSearchProvider

__all__ = [
    "DecisionTraceRepository",
    "Generator",
    "HallucinationChecker",
    "QueryRewriter",
    "RelevanceGrader",
    "Retriever",
    "WebSearchProvider",
]
