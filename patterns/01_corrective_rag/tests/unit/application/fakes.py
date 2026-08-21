"""Handwritten deterministic test fakes for Domain capability ports.

These fakes structurally satisfy the Domain Protocols without inheritance or mock frameworks,
enabling deterministic, unit-testable Application graph execution.
"""

from collections.abc import Sequence

from corrective_rag.domain.entities.answer import Answer, AnswerStatus
from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.graded_document import GradedDocument
from corrective_rag.domain.entities.question import Question


class FakeRetriever:
    """Fake retriever returning predefined documents and recording received questions.

    Note: Satisfies Retriever port structurally. Does NOT inherit from Retriever.
    """

    def __init__(self, documents: Sequence[Document] | None = None) -> None:
        self._documents = tuple(documents or [])
        self.received_questions: list[Question] = []

    def retrieve(self, question: Question) -> Sequence[Document]:
        self.received_questions.append(question)
        return self._documents


class FakeRelevanceGrader:
    """Fake relevance grader recording evaluated documents.

    If `relevant_document_sources` is provided, only documents matching those source strings
    are graded as relevant; otherwise, all documents are graded according to `default_is_relevant`.

    Note: Satisfies RelevanceGrader port structurally. Does NOT inherit from RelevanceGrader.
    """

    def __init__(
        self,
        default_is_relevant: bool = True,
        relevant_document_sources: Sequence[str] | None = None,
    ) -> None:
        self._default_is_relevant = default_is_relevant
        self._relevant_sources = (
            set(relevant_document_sources) if relevant_document_sources is not None else None
        )
        self.received_grades: list[tuple[Question, Document]] = []

    def grade(self, question: Question, document: Document) -> GradedDocument:
        self.received_grades.append((question, document))
        is_relevant = (
            document.source in self._relevant_sources
            if self._relevant_sources is not None
            else self._default_is_relevant
        )
        return GradedDocument(
            document=document,
            is_relevant=is_relevant,
            reason=f"Fake grading result for {document.source}",
        )


class FakeGenerator:
    """Fake generator returning predefined Answer(s) and recording call inputs.

    Note: Satisfies Generator port structurally. Does NOT inherit from Generator.
    """

    def __init__(
        self,
        answer: Answer | None = None,
        answers: Sequence[Answer] | None = None,
    ) -> None:
        if answers is not None:
            if not answers:
                raise ValueError("answers must contain at least one Answer")
            self._answers = tuple(answers)
        elif answer is not None:
            self._answers = (answer,)
        else:
            self._answers = (
                Answer(
                    text="Fake generated response grounded in evidence.",
                    status=AnswerStatus.ANSWERED,
                ),
            )
        self.received_calls: list[tuple[Question, Sequence[Document]]] = []

    def generate(self, question: Question, documents: Sequence[Document]) -> Answer:
        self.received_calls.append((question, tuple(documents)))
        call_index = len(self.received_calls) - 1
        if call_index < len(self._answers):
            return self._answers[call_index]
        return self._answers[-1]


class FakeHallucinationChecker:
    """Fake hallucination checker returning predefined boolean(s) and recording checks.

    Note: Satisfies HallucinationChecker port structurally. Does NOT inherit from HallucinationChecker.
    """

    def __init__(
        self,
        is_supported: bool = True,
        results: Sequence[bool] | None = None,
    ) -> None:
        if results is not None:
            if not results:
                raise ValueError("results must contain at least one boolean result")
            self._results = tuple(results)
        else:
            self._results = (is_supported,)
        self.received_checks: list[tuple[Answer, Sequence[Document]]] = []

    def is_supported(self, answer: Answer, documents: Sequence[Document]) -> bool:
        self.received_checks.append((answer, tuple(documents)))
        check_index = len(self.received_checks) - 1
        if check_index < len(self._results):
            return self._results[check_index]
        return self._results[-1]


class FakeQueryRewriter:
    """Fake query rewriter returning a predefined Question and recording input questions.

    Note: Satisfies QueryRewriter port structurally. Does NOT inherit from QueryRewriter.
    """

    def __init__(self, rewritten_question: Question | None = None) -> None:
        self._rewritten_question = rewritten_question or Question(
            text="Fake rewritten search query"
        )
        self.received_questions: list[Question] = []

    def rewrite(self, question: Question) -> Question:
        self.received_questions.append(question)
        return self._rewritten_question


class FakeWebSearchProvider:
    """Fake web search provider returning predefined documents and recording search questions.

    Note: Satisfies WebSearchProvider port structurally. Does NOT inherit from WebSearchProvider.
    """

    def __init__(self, documents: Sequence[Document] | None = None) -> None:
        self._documents = tuple(documents or [])
        self.received_questions: list[Question] = []

    def search(self, question: Question) -> Sequence[Document]:
        self.received_questions.append(question)
        return self._documents
