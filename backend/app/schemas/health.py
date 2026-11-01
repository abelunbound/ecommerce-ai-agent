"""Health check response."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Backend liveness payload."""

    status: str
