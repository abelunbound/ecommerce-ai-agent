"""Health route."""

from app.schemas.health import HealthResponse
from app.services.health import health_status
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Report that the API process is up."""
    return HealthResponse(status=health_status())
