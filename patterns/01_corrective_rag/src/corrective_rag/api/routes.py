"""FastAPI HTTP route handlers for Corrective RAG."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from corrective_rag.api.models import (
    DecisionTraceStepResponse,
    HealthResponse,
    QuestionRequest,
    QuestionResponse,
)
from corrective_rag.application.application import CorrectiveRAGApplication
from corrective_rag.application.graph_state import GraphState
from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.question import Question


def get_application(request: Request) -> CorrectiveRAGApplication:
    """FastAPI dependency extracting the pre-assembled CorrectiveRAGApplication from app state."""
    app_instance: CorrectiveRAGApplication | None = getattr(
        request.app.state, "application", None
    )
    if app_instance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application runtime has not been configured.",
        )
    return app_instance


router = APIRouter()


def _map_final_state_to_response(final_state: GraphState) -> QuestionResponse:
    """Validates terminal application state and maps it to a QuestionResponse DTO.

    Strictly validates that final_state satisfies the expected Application contract.
    Does NOT manufacture fallback answers or coerce types for malformed state.

    Args:
        final_state: Completed application GraphState dictionary.

    Returns:
        QuestionResponse DTO.

    Raises:
        TypeError, KeyError, ValueError: If final_state is missing required keys or contains malformed types.
    """
    if not isinstance(final_state, dict):
        raise TypeError("Workflow final state must be a dictionary.")

    if "answer" not in final_state:
        raise KeyError("Workflow final state is missing required 'answer' key.")
    answer = final_state["answer"]
    if not isinstance(answer, Answer):
        raise TypeError("Workflow final state 'answer' must be an Answer instance.")

    if answer.status == AnswerStatus.ANSWERED:
        answer_status_str = "answered"
    elif answer.status == AnswerStatus.UNSUPPORTED:
        answer_status_str = "unsupported"
    else:
        raise ValueError(f"Unknown AnswerStatus: {answer.status}")

    if "is_supported" not in final_state:
        raise KeyError("Workflow final state is missing required 'is_supported' key.")
    is_supported_val = final_state["is_supported"]
    if type(is_supported_val) is not bool:
        raise TypeError("Workflow final state 'is_supported' must be a boolean.")

    if "generation_attempts" not in final_state:
        raise KeyError("Workflow final state is missing required 'generation_attempts' key.")
    attempts_val = final_state["generation_attempts"]
    if type(attempts_val) is not int or attempts_val < 0:
        raise TypeError("Workflow final state 'generation_attempts' must be a non-negative integer.")

    if "trace" not in final_state:
        raise KeyError("Workflow final state is missing required 'trace' key.")
    trace_obj = final_state["trace"]
    if not isinstance(trace_obj, DecisionTrace):
        raise TypeError("Workflow final state 'trace' must be a DecisionTrace instance.")

    decision_trace_dtos = [
        DecisionTraceStepResponse(step=step.name, detail=step.detail)
        for step in trace_obj.steps
    ]

    return QuestionResponse(
        answer=answer.text,
        status=answer_status_str,
        is_supported=is_supported_val,
        generation_attempts=attempts_val,
        decision_trace=decision_trace_dtos,
    )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check() -> HealthResponse:
    """Process-level liveness health check endpoint.

    Returns HTTP 200 OK if the web server process is responsive. Does NOT check downstream
    database connections, vector indexes, external search providers, or LLM services.
    """
    return HealthResponse(status="ok")


@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
def ask_question(
    request_dto: QuestionRequest,
    application: CorrectiveRAGApplication = Depends(get_application),
) -> QuestionResponse:
    """Submits a troubleshooting question to the Corrective RAG application runtime.

    Delegates execution strictly to CorrectiveRAGApplication.run(question), which manages
    LangGraph orchestration and decision trace persistence internally.

    Args:
        request_dto: Validated HTTP request DTO containing the user's question.
        application: Injected CorrectiveRAGApplication runtime instance.

    Returns:
        QuestionResponse DTO containing generated answer, status, grounding result,
        attempts count, and inline decision trace.

    Raises:
        HTTPException: HTTP 500 if an unhandled operational exception or contract violation occurs.
    """
    domain_question = Question(text=request_dto.question)

    try:
        final_state = application.run(domain_question)
        return _map_final_state_to_response(final_state)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the question.",
        ) from exc
