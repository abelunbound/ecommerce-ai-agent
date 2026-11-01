"""Dash health page reads GET /health through httpx."""

import httpx
from app.api_client import fetch_health
from app.layout import health_line


def test_page_reports_backend_health() -> None:
    """The page text is the status returned by the backend."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/health"
        return httpx.Response(200, json={"status": "ok"})

    status = fetch_health(transport=httpx.MockTransport(handler))

    assert health_line(status) == "Backend health: ok"
