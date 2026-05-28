from fastapi import APIRouter

from app.core.config import settings
from app.schemas.system import HealthResponse, ReadinessResponse, RootResponse
from app.services.readiness import build_readiness_response


router = APIRouter(tags=["system"])


@router.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        name=settings.app_name,
        version=settings.app_version,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name)


@router.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    return build_readiness_response(settings)
