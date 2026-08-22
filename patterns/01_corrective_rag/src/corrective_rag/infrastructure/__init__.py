"""Infrastructure Layer.

Implements Domain Ports using concrete external technology adapters (e.g., Chroma, Groq, Tavily).
Isolates third-party vendor SDK dependencies from the Domain and Application layers.
"""

from corrective_rag.infrastructure.verification import GroqHallucinationChecker

__all__ = ["GroqHallucinationChecker"]
