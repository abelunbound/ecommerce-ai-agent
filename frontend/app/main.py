"""Dash entrypoint."""

from app.layout import create_app

app = create_app()


def main() -> None:
    """Serve the Dash page."""
    app.run(host="127.0.0.1", port=8050, debug=False)


if __name__ == "__main__":
    main()
