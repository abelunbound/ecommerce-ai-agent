"""Settings fail fast when a required value is missing."""

import importlib

import app.core.config as config
import pytest


def test_missing_openai_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A blank OPENAI_API_KEY stops startup and names that variable."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *_args, **_kwargs: False)
    reloaded = importlib.reload(config)

    try:
        with pytest.raises(reloaded.SettingsError, match="OPENAI_API_KEY"):
            reloaded.check_required()
    finally:
        monkeypatch.undo()
        importlib.reload(reloaded)
