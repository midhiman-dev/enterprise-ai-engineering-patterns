"""Evaluation models for golden scenario execution and reporting.

Provides data structures representing evaluation evidence, scenario execution results,
and overall evaluation summary reports outside the core Domain layer.
"""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LocalRelevanceRecord:
    """Represents relevance evaluation metadata for a candidate local document.

    Attributes:
        source: Primary source identifier of the document chunk.
        title: Document title if present in document metadata.
        relevance_result: Boolean relevance decision from relevance grader.
        score: Optional numeric relevance score.
        reason: Optional text explanation for relevance decision.
    """

    source: str
    title: str | None
    relevance_result: bool
    score: float | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Returns standard dictionary representation."""
        return asdict(self)


@dataclass
class ScenarioResult:
    """Represents the complete observational result of running a single golden scenario.

    Attributes:
        scenario_id: Identifier for the scenario (e.g. 'Q1_LOCAL_KNOWN').
        query: User input query string.
        started_at_utc: ISO timestamp when execution started.
        completed_at_utc: ISO timestamp when execution completed.
        elapsed_ms: Execution duration in milliseconds.
        model: LLM provider model identifier used during execution.
        final_status: Terminal status ('ANSWERED', 'UNSUPPORTED', or 'ERROR').
        final_answer: Final answer text generated or safe refusal response.
        generation_attempts: Number of answer generation attempts executed.
        observed_trace_steps: List of graph node step names executed during workflow.
        used_web_search: Whether external web search step was executed.
        rewritten_query: Query reformulation if rewrite_query was executed, else None.
        local_relevance: Records of document relevance evaluation.
        final_sources: List of source identifiers or URLs present in final evidence.
        supported: Grounding verification result if observable.
        expected_behavior: Descriptive text of intended behavioral properties.
        evaluation_outcome: Evaluation classification ('PASS', 'DIVERGENCE', 'ERROR').
        evaluation_notes: Descriptive notes explaining evaluation classification.
    """

    scenario_id: str
    query: str
    started_at_utc: str
    completed_at_utc: str
    elapsed_ms: float
    model: str
    final_status: str
    final_answer: str
    generation_attempts: int
    observed_trace_steps: list[str]
    used_web_search: bool
    rewritten_query: str | None
    local_relevance: list[LocalRelevanceRecord]
    final_sources: list[str]
    supported: bool | None
    expected_behavior: str
    evaluation_outcome: str
    evaluation_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Returns standard JSON-serializable dictionary representation."""
        return {
            "scenario_id": self.scenario_id,
            "query": self.query,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "model": self.model,
            "final_status": self.final_status,
            "final_answer": self.final_answer,
            "generation_attempts": self.generation_attempts,
            "observed_trace_steps": self.observed_trace_steps,
            "used_web_search": self.used_web_search,
            "rewritten_query": self.rewritten_query,
            "local_relevance": [rec.to_dict() for rec in self.local_relevance],
            "final_sources": self.final_sources,
            "supported": self.supported,
            "expected_behavior": self.expected_behavior,
            "evaluation_outcome": self.evaluation_outcome,
            "evaluation_notes": self.evaluation_notes,
        }


@dataclass
class GoldenEvaluationReport:
    """Represents a complete golden scenario evaluation report.

    Attributes:
        metadata: High-level configuration and environment metadata.
        scenario_results: List of per-scenario evaluation results.
        summary: Aggregated pass/divergence/error counts.
    """

    metadata: dict[str, Any]
    scenario_results: list[ScenarioResult]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Returns standard JSON-serializable dictionary representation."""
        return {
            "metadata": self.metadata,
            "scenario_results": [res.to_dict() for res in self.scenario_results],
            "summary": self.summary,
        }
