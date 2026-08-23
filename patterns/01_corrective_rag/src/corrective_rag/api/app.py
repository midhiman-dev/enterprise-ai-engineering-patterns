"""FastAPI application factory for Corrective RAG."""

from fastapi import FastAPI

from corrective_rag.api.routes import router
from corrective_rag.application.application import CorrectiveRAGApplication
from corrective_rag.composition.container import build_application


def create_api(
    application: CorrectiveRAGApplication | None = None,
) -> FastAPI:
    """Creates and configures the FastAPI web application instance.

    Args:
        application: Optional pre-assembled CorrectiveRAGApplication instance.
            If None, calls build_application() from the composition root to build
            the production runtime instance once upon API initialization.

    Returns:
        Configured FastAPI web application instance ready for request serving or testing.
    """
    if application is None:
        application = build_application()

    app = FastAPI(
        title="Corrective RAG API",
        description="HTTP API interface for Corrective RAG Kubernetes troubleshooting workflow.",
        version="0.1.0",
    )

    app.state.application = application
    app.include_router(router)

    return app
