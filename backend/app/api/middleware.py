"""Bind a request id and write one access line per request."""

import logging
import re
import time
import uuid

from app.core.logging import RequestIdFilter
from app.core.request_context import request_id_var
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)
logger.addFilter(RequestIdFilter())

_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestContextMiddleware:
    """Set the request id for the call and log method, path and status once."""

    def __init__(self, app: ASGIApp) -> None:
        """Store the next ASGI app."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Assign the request id, then log the finished call."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id(scope)
        token = request_id_var.set(request_id)
        status_code = 500
        started = time.perf_counter()

        async def send_with_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            logger.exception("Unhandled error")
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            path = scope.get("path", "")
            level = logging.DEBUG if path == "/health" else logging.INFO
            logger.log(
                level,
                "%s %s %s duration_ms=%s",
                scope.get("method", "-"),
                path,
                status_code,
                duration_ms,
            )
            request_id_var.reset(token)


def _request_id(scope: Scope) -> str:
    """Keep a safe inbound id, otherwise generate one."""
    raw = _header(scope, b"x-request-id")
    if raw and _REQUEST_ID.fullmatch(raw):
        return raw
    return uuid.uuid4().hex


def _header(scope: Scope, name: bytes) -> str:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return value.decode("latin-1")
    return ""
