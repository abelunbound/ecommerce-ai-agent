"""Dash layout for the health page."""

import httpx
from dash import Dash, Input, Output, html

from app.api_client import fetch_health


def health_line(status: str) -> str:
    """Format the status the page shows."""
    return f"Backend health: {status}"


def create_app() -> Dash:
    """Build the page that reports backend health."""
    app = Dash(__name__)
    app.title = "Lumen & Oak"
    app.layout = html.Div(
        [
            html.H1("Lumen & Oak"),
            html.P(id="health-status", children="Checking backend health..."),
        ]
    )

    @app.callback(Output("health-status", "children"), Input("health-status", "id"))
    def show_health(_: str) -> str:
        """Load /health and render it."""
        try:
            status = fetch_health()
        except httpx.HTTPError:
            return "Backend health: unreachable"
        return health_line(status)

    return app
