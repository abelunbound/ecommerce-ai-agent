"""Settings fail fast when a required value is missing."""

import app.core.config as config
import pytest


def test_missing_openai_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A blank OPENAI_API_KEY stops startup and names that variable."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(config.SettingsError, match="OPENAI_API_KEY"):
        config.check_required()
