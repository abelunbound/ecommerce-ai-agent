"""The only place the frontend talks HTTP. Callbacks call these functions, never httpx."""

from typing import Any

import httpx

from app.config import BACKEND_URL


def _get(
    path: str,
    *,
    transport: httpx.BaseTransport | None = None,
    **params: Any,
) -> Any:
    """GET a backend path and return the JSON body."""
    query = {key: value for key, value in params.items() if value not in (None, "")}
    root = BACKEND_URL.rstrip("/")
    with httpx.Client(base_url=root, timeout=5.0, transport=transport) as client:
        response = client.get(path, params=query)
        response.raise_for_status()
    return response.json()


def fetch_health(*, transport: httpx.BaseTransport | None = None) -> str:
    """GET /health and return the status string."""
    status = _get("/health", transport=transport)["status"]
    if not isinstance(status, str):
        raise httpx.HTTPError("Health status was not a string")
    return status
