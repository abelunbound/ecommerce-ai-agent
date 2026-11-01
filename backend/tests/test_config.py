"""Settings fail fast when a required value is missing."""

import pytest
from app.core.config import SettingsError, load_settings


def test_missing_openai_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A blank OPENAI_API_KEY stops startup and names that variable."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SettingsError, match="OPENAI_API_KEY"):
        load_settings(_env_file=None)
