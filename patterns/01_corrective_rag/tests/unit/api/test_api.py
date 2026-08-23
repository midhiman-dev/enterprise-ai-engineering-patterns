"""Unit tests for FastAPI HTTP transport boundary."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from corrective_rag.api.app import create_api
from corrective_rag.application.application import CorrectiveRAGApplication
from corrective_rag.application.workflow import build_graph
from corrective_rag.application.workflow_dependencies import WorkflowDependencies
from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.decision_trace import DecisionTrace
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question
from tests.unit.application.fakes import (
    FakeDecisionTraceRepository,
    FakeGenerator,
    FakeHallucinationChecker,
    FakeQueryRewriter,
    FakeRelevanceGrader,
    FakeRetriever,
    FakeWebSearchProvider,
)


def build_test_application(
    retriever_docs: list[Document] | None = None,
    default_is_relevant: bool = True,
    generator_answers: list[Answer] | None = None,
    checker_results: list[bool] | None = None,
    web_docs: list[Document] | None = None,
) -> tuple[CorrectiveRAGApplication, FakeDecisionTraceRepository]:
    """Helper creating a test CorrectiveRAGApplication backed by handwritten fakes."""
    fake_repo = FakeDecisionTraceRepository()
    doc = Document(content="Kubernetes troubleshooting doc", source="k8s.md")

    deps = WorkflowDependencies(
        retriever=FakeRetriever(documents=retriever_docs or [doc]),
        relevance_grader=FakeRelevanceGrader(default_is_relevant=default_is_relevant),
        query_rewriter=FakeQueryRewriter(),
        generator=FakeGenerator(
            answers=generator_answers
            or [
                Answer(
                    text="Grounded answer for Kubernetes pod issues.",
                    status=AnswerStatus.ANSWERED,
                )
            ]
        ),
        web_search_provider=FakeWebSearchProvider(documents=web_docs or [doc]),
        hallucination_checker=FakeHallucinationChecker(
            results=checker_results or [True]
        ),
    )
    graph = build_graph(deps)
    app_instance = CorrectiveRAGApplication(graph=graph, repository=fake_repo)
    return app_instance, fake_repo


class ErrorRaisingApplication(CorrectiveRAGApplication):
    """Test fake application subclass that raises an exception on run()."""

    def run(self, question: Question, trace: object = None) -> object:
        raise RuntimeError("GROQ_API_KEY_SECRET_12345 database connection failed")


class MalformedStateApplication(CorrectiveRAGApplication):
    """Test fake application subclass that returns custom (potentially malformed) state dict."""

    def __init__(self, state_to_return: dict) -> None:
        self.state_to_return = state_to_return

    def run(self, question: Question, trace: object = None) -> dict:
        return self.state_to_return


def _valid_terminal_state() -> dict:
    """Returns a valid terminal GraphState dictionary baseline for testing."""
    return {
        "question": Question(text="Valid question"),
        "rewritten_question": None,
        "documents": [],
        "graded_documents": [],
        "answer": Answer(text="Valid answer", status=AnswerStatus.ANSWERED),
        "is_supported": True,
        "generation_attempts": 1,
        "trace": DecisionTrace(),
    }


def test_health_check_returns_200_ok() -> None:
    """Verifies GET /health returns HTTP 200 {"status": "ok"}."""
    app_instance, fake_repo = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert len(fake_repo.saved_traces) == 0


def test_ask_question_straight_path_returns_200_and_mapped_dto() -> None:
    """Verifies POST /questions returns 200 with mapped fields and inline decision trace."""
    app_instance, fake_repo = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    payload = {"question": "Why does kubectl get pods show CrashLoopBackOff?"}
    response = client.post("/questions", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Grounded answer for Kubernetes pod issues."
    assert data["status"] == "answered"
    assert data["is_supported"] is True
    assert data["generation_attempts"] == 1

    steps = [item["step"] for item in data["decision_trace"]]
    assert steps == ["retrieve", "grade_documents", "generate", "hallucination_check"]
    assert len(fake_repo.saved_traces) == 1


def test_ask_question_missing_question_returns_422() -> None:
    """Verifies missing question field is rejected with HTTP 422."""
    app_instance, _ = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    response = client.post("/questions", json={})

    assert response.status_code == 422


def test_ask_question_blank_question_returns_422() -> None:
    """Verifies blank question string is rejected with HTTP 422."""
    app_instance, _ = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    response = client.post("/questions", json={"question": ""})

    assert response.status_code == 422


def test_ask_question_whitespace_only_question_returns_422() -> None:
    """Verifies whitespace-only question is rejected with HTTP 422."""
    app_instance, _ = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    response = client.post("/questions", json={"question": "   \n\t  "})

    assert response.status_code == 422


def test_ask_question_non_string_question_returns_422() -> None:
    """Verifies integer question value is rejected by Pydantic with HTTP 422 without implicit coercion."""
    app_instance, _ = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    response = client.post("/questions", json={"question": 123})

    assert response.status_code == 422


def test_ask_question_corrective_path_trace_steps() -> None:
    """Verifies corrective route exposes web search steps in decision trace DTO."""
    app_instance, _ = build_test_application(default_is_relevant=False)
    api = create_api(application=app_instance)
    client = TestClient(api)

    payload = {"question": "How do I handle pod eviction under K8s 1.32?"}
    response = client.post("/questions", json=payload)

    assert response.status_code == 200
    data = response.json()
    steps = [item["step"] for item in data["decision_trace"]]
    assert steps == [
        "retrieve",
        "grade_documents",
        "rewrite_query",
        "web_search",
        "generate",
        "hallucination_check",
    ]


def test_ask_question_safe_refusal_returns_200_with_unsupported_status() -> None:
    """Verifies AnswerStatus.UNSUPPORTED returns HTTP 200 OK with status="unsupported"."""
    refusal_answer = Answer(
        text="I cannot answer this question as the premise is unsupported.",
        status=AnswerStatus.UNSUPPORTED,
    )
    app_instance, _ = build_test_application(
        generator_answers=[refusal_answer, refusal_answer],
        checker_results=[False, False],
    )
    api = create_api(application=app_instance)
    client = TestClient(api)

    payload = {"question": "What does --enable-quantum-scheduler flag do?"}
    response = client.post("/questions", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported"
    assert data["is_supported"] is False
    assert data["answer"] == "I cannot provide a supported answer based on the available evidence."
    steps = [item["step"] for item in data["decision_trace"]]
    assert "safe_refusal" in steps


def test_ask_question_operational_failure_returns_500_without_leaking_secrets() -> None:
    """Verifies runtime execution failure returns HTTP 500 and does not leak raw secrets."""
    graph = build_graph(
        WorkflowDependencies(
            retriever=FakeRetriever(),
            relevance_grader=FakeRelevanceGrader(),
            query_rewriter=FakeQueryRewriter(),
            generator=FakeGenerator(),
            web_search_provider=FakeWebSearchProvider(),
            hallucination_checker=FakeHallucinationChecker(),
        )
    )
    error_app = ErrorRaisingApplication(graph=graph, repository=FakeDecisionTraceRepository())
    api = create_api(application=error_app)
    client = TestClient(api)

    payload = {"question": "What happens when system fails?"}
    response = client.post("/questions", json=payload)

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "GROQ_API_KEY_SECRET_12345" not in data["detail"]
    assert "database connection failed" not in data["detail"]
    assert data["detail"] == "An internal error occurred while processing the question."


def test_application_reused_across_multiple_requests() -> None:
    """Verifies the exact same CorrectiveRAGApplication instance is reused across API requests."""
    app_instance, fake_repo = build_test_application()
    api = create_api(application=app_instance)
    client = TestClient(api)

    client.post("/questions", json={"question": "Question one"})
    client.post("/questions", json={"question": "Question two"})

    assert len(fake_repo.saved_traces) == 2
    assert api.state.application is app_instance


# -----------------------------------------------------------------------------
# Malformed Terminal State Response Contract Hardening Tests
# -----------------------------------------------------------------------------


def test_ask_question_missing_answer_returns_500() -> None:
    """Verifies missing 'answer' key in final state returns HTTP 500 without manufacturing fallback."""
    state = _valid_terminal_state()
    del state["answer"]
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "An internal error occurred while processing the question."
    assert "No answer generated." not in str(data)


def test_ask_question_answer_none_returns_500() -> None:
    """Verifies None 'answer' in final state returns HTTP 500."""
    state = _valid_terminal_state()
    state["answer"] = None
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


def test_ask_question_wrong_answer_type_returns_500() -> None:
    """Verifies string 'answer' (wrong type) in final state returns HTTP 500."""
    state = _valid_terminal_state()
    state["answer"] = "some string answer"
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


def test_ask_question_missing_is_supported_returns_500() -> None:
    """Verifies missing 'is_supported' key in final state returns HTTP 500."""
    state = _valid_terminal_state()
    del state["is_supported"]
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


def test_ask_question_is_supported_none_returns_500() -> None:
    """Verifies None 'is_supported' in final state returns HTTP 500."""
    state = _valid_terminal_state()
    state["is_supported"] = None
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


@pytest.mark.parametrize("invalid_value", ["false", 0, 1])
def test_ask_question_wrong_is_supported_type_returns_500(invalid_value: Any) -> None:
    """Verifies non-boolean is_supported values (str, int) return HTTP 500 without truthiness coercion."""
    state = _valid_terminal_state()
    state["is_supported"] = invalid_value
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


def test_ask_question_missing_generation_attempts_returns_500() -> None:
    """Verifies missing 'generation_attempts' key in final state returns HTTP 500."""
    state = _valid_terminal_state()
    del state["generation_attempts"]
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


@pytest.mark.parametrize("invalid_value", ["1", True])
def test_ask_question_invalid_generation_attempts_type_returns_500(
    invalid_value: Any,
) -> None:
    """Verifies non-integer generation_attempts values (str, bool) return HTTP 500."""
    state = _valid_terminal_state()
    state["generation_attempts"] = invalid_value
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


def test_ask_question_invalid_generation_attempts_range_returns_500() -> None:
    """Verifies negative generation_attempts value (-1) returns HTTP 500."""
    state = _valid_terminal_state()
    state["generation_attempts"] = -1
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


def test_ask_question_missing_trace_returns_500() -> None:
    """Verifies missing 'trace' key in final state returns HTTP 500."""
    state = _valid_terminal_state()
    del state["trace"]
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."


@pytest.mark.parametrize("invalid_value", [[], "trace"])
def test_ask_question_wrong_trace_type_returns_500(invalid_value: Any) -> None:
    """Verifies non-DecisionTrace 'trace' values (list, str) return HTTP 500."""
    state = _valid_terminal_state()
    state["trace"] = invalid_value
    api = create_api(application=MalformedStateApplication(state))
    client = TestClient(api)

    response = client.post("/questions", json={"question": "Valid question"})

    assert response.status_code == 500
    assert response.json()["detail"] == "An internal error occurred while processing the question."
