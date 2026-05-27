from fastapi import FastAPI

from app.schemas import HealthResponse


APP_TITLE = "GuardedRAG API"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description="Source-grounded RAG API prototype.",
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="guardedrag")

    return app


app = create_app()

