from app.core.config import Settings
from app.schemas.system import DependencyCheck, ReadinessResponse


def build_readiness_response(settings: Settings) -> ReadinessResponse:
    checks = [
        DependencyCheck(
            name="configuration",
            available=True,
            detail="Application settings loaded.",
        ),
        DependencyCheck(
            name="vector_store_path",
            available=bool(settings.vector_store_path),
            detail=str(settings.vector_store_path),
        ),
        DependencyCheck(
            name="retrieval_settings",
            available=settings.top_k >= 1 and 0 <= settings.similarity_threshold <= 1,
            detail=(
                f"top_k={settings.top_k}, "
                f"similarity_threshold={settings.similarity_threshold}"
            ),
        ),
        DependencyCheck(
            name="chunking_settings",
            available=settings.chunk_size > settings.chunk_overlap >= 0,
            detail=(
                f"chunk_size={settings.chunk_size}, "
                f"chunk_overlap={settings.chunk_overlap}"
            ),
        ),
    ]

    status = "ready" if all(check.available for check in checks) else "not_ready"
    return ReadinessResponse(
        status=status,
        service=settings.service_name,
        checks=checks,
    )
