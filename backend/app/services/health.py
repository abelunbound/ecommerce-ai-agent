"""Liveness status for the API."""


def health_status() -> str:
    """Return the backend liveness value."""
    return "ok"
