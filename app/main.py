from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Source-grounded RAG API prototype.",
    )

    app.include_router(router)
    return app


app = create_app()
