from pathlib import Path

from app.core.config import Settings
from app.services.readiness import build_readiness_response


def test_readiness_reports_not_ready_for_invalid_chunking_settings() -> None:
    settings = Settings(
        vector_store_path=Path("data/vector_store"),
        chunk_size=800,
        chunk_overlap=800,
    )

    response = build_readiness_response(settings)

    assert response.status == "not_ready"
    failed_checks = {
        check.name
        for check in response.checks
        if not check.available
    }
    assert failed_checks == {"chunking_settings"}

