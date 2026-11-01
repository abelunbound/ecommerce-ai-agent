"""FastAPI application."""

from fastapi import FastAPI

from app.api.middleware import RequestContextMiddleware
from app.api.router import router
from app.core.config import load_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Build the API with request logging configured once."""
    settings = load_settings()
    configure_logging(settings)
    app = FastAPI(title="Lumen & Oak")
    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)
    return app


app = create_app()
