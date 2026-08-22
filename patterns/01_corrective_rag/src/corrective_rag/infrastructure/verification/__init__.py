"""Verification infrastructure package for Corrective RAG.

Exports concrete adapters for evidence grounding and support verification.
"""

from corrective_rag.infrastructure.verification.groq_hallucination_checker import (
    GroqGroundingResult,
    GroqHallucinationChecker,
    build_grounding_check_messages,
    parse_grounding_result,
)

__all__ = [
    "GroqGroundingResult",
    "GroqHallucinationChecker",
    "build_grounding_check_messages",
    "parse_grounding_result",
]
