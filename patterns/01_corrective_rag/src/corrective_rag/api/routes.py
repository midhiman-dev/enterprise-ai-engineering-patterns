"""FastAPI HTTP route handlers for Corrective RAG."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from corrective_rag.api.models import (
    DecisionTraceStepResponse,
    HealthResponse,
    QuestionRequest,
    QuestionResponse,
)
from corrective_rag.application.application import CorrectiveRAGApplication
from corrective_rag.domain.entities.answer import AnswerStatus
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
        HTTPException: HTTP 500 if an unhandled operational exception occurs during processing.
    """
    domain_question = Question(text=request_dto.question)

    try:
        final_state = application.run(domain_question)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the question.",
        ) from exc

    final_answer = final_state.get("answer")
    if final_answer is not None:
        answer_text = final_answer.text
        answer_status_str = final_answer.status.value
    else:
        answer_text = "No answer generated."
        answer_status_str = AnswerStatus.UNSUPPORTED.value

    raw_supported = final_state.get("is_supported")
    is_supported_bool = bool(raw_supported) if raw_supported is not None else False
    generation_attempts = final_state.get("generation_attempts", 0)

    trace_obj = final_state.get("trace")
    if trace_obj is not None:
        decision_trace_dtos = [
            DecisionTraceStepResponse(step=step.name, detail=step.detail)
            for step in trace_obj.steps
        ]
    else:
        decision_trace_dtos = []

    return QuestionResponse(
        answer=answer_text,
        status=answer_status_str,
        is_supported=is_supported_bool,
        generation_attempts=generation_attempts,
        decision_trace=decision_trace_dtos,
    )
