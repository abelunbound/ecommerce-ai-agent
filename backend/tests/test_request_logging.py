"""Request ids are assigned, echoed and cleared."""

import logging

import pytest
from app.api.middleware import RequestContextMiddleware
from app.core.request_context import get_request_id
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/orders")
    def orders() -> dict[str, str]:
        logging.getLogger("app.api.middleware").info("inside request")
        return {"ok": "yes"}

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    return app


def test_generated_id_is_echoed_and_cleared() -> None:
    """A missing inbound id is generated, returned, then cleared."""
    response = TestClient(_app()).get("/orders")

    request_id = response.headers["x-request-id"]
    assert len(request_id) == 32
    assert get_request_id() == "-"


def test_valid_inbound_id_is_kept() -> None:
    """A safe inbound id is reused on the response."""
    response = TestClient(_app()).get("/orders", headers={"X-Request-ID": "abc12345"})

    assert response.headers["x-request-id"] == "abc12345"


def test_invalid_inbound_ids_are_replaced() -> None:
    """Spaces, newlines and the wrong length do not reach the log."""
    client = TestClient(_app())
    for value in ("short", "has space", "bad\nid", "x" * 65):
        response = client.get("/orders", headers={"X-Request-ID": value})
        assert response.headers["x-request-id"] != value
        assert " " not in response.headers["x-request-id"]
        assert "\n" not in response.headers["x-request-id"]


def test_log_inside_request_carries_the_id(caplog: pytest.LogCaptureFixture) -> None:
    """A log emitted while handling the request stores that request id."""
    with caplog.at_level(logging.INFO, logger="app.api.middleware"):
        response = TestClient(_app()).get("/orders", headers={"X-Request-ID": "abc12345"})

    inside = [record for record in caplog.records if record.message == "inside request"]
    access = [record for record in caplog.records if "duration_ms=" in record.message]
    assert inside[0].request_id == "abc12345"  # type: ignore[attr-defined]
    assert access[0].message.startswith("GET /orders 200 ")
    assert "token" not in access[0].message
    assert response.headers["x-request-id"] == "abc12345"
    assert get_request_id() == "-"


def test_query_string_and_body_are_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    """The access line keeps the path and drops the query string and body."""
    with caplog.at_level(logging.INFO, logger="app.api.middleware"):
        TestClient(_app()).post("/orders?token=Hunter2!", json={"password": "Hunter2!"})

    access = [record.message for record in caplog.records if "duration_ms=" in record.message]
    assert access
    assert "Hunter2!" not in access[0]
    assert "/orders?" not in access[0]
    assert access[0].startswith("POST /orders ")


def test_health_is_debug(caplog: pytest.LogCaptureFixture) -> None:
    """Health checks are logged at debug so they stay out of the info stream."""
    with caplog.at_level(logging.DEBUG, logger="app.api.middleware"):
        TestClient(_app()).get("/health")

    health = [record for record in caplog.records if record.message.startswith("GET /health")]
    assert health
    assert health[0].levelno == logging.DEBUG


def test_unhandled_exception_is_logged_once(caplog: pytest.LogCaptureFixture) -> None:
    """The traceback is logged one time and the error is still raised."""
    client = TestClient(_app(), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="app.api.middleware"):
        response = client.get("/boom")

    errors = [record for record in caplog.records if record.exc_info]
    assert response.status_code == 500
    assert len(errors) == 1
