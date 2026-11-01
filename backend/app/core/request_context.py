"""Request id for the current API call."""

from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Return the current request id, or `-` outside a request."""
    return request_id_var.get()
