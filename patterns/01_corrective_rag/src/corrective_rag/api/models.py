"""Data Transfer Objects (DTOs) for the FastAPI HTTP transport boundary."""

from pydantic import BaseModel, field_validator


class QuestionRequest(BaseModel):
    """HTTP request payload for asking a troubleshooting question.

    Invariants:
        - question must be a non-empty and non-whitespace string.
        - preserves exact original user wording.
    """

    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Validates that question text is non-empty and not whitespace-only."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Question text cannot be empty or whitespace-only.")
        return value


class DecisionTraceStepResponse(BaseModel):
    """Inline HTTP DTO representing a single recorded step in the decision trace.

    Attributes:
        step: Semantic name of the workflow execution step (e.g., 'retrieve', 'generate').
        detail: Optional additional detail or context recorded for the step.
    """

    step: str
    detail: str | None = None


class QuestionResponse(BaseModel):
    """HTTP response payload containing answer, execution status, and decision trace.

    Attributes:
        answer: Generated answer text or safe refusal explanation.
        status: API status string ('answered' or 'unsupported').
        is_supported: Grounding verification outcome boolean.
        generation_attempts: Number of answer generation attempts executed.
        decision_trace: Ordered sequence of execution steps recorded during workflow.
    """

    answer: str
    status: str
    is_supported: bool
    generation_attempts: int
    decision_trace: list[DecisionTraceStepResponse]


class HealthResponse(BaseModel):
    """HTTP response payload for process-level liveness health check."""

    status: str = "ok"
