"""Workflow Dependencies container.

Provides explicit dependency injection of Domain ports required by Application node handlers.
"""

from dataclasses import dataclass

from corrective_rag.domain.ports.generator import Generator
from corrective_rag.domain.ports.hallucination_checker import HallucinationChecker
from corrective_rag.domain.ports.relevance_grader import RelevanceGrader
from corrective_rag.domain.ports.retriever import Retriever


@dataclass(frozen=True)
class WorkflowDependencies:
    """Container holding domain ports required by the Pass-3 straight-path workflow.

    Dependencies are injected explicitly into node factory functions during graph construction.
    """

    retriever: Retriever
    relevance_grader: RelevanceGrader
    generator: Generator
    hallucination_checker: HallucinationChecker
