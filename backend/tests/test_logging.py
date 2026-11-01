"""Log format, startup settings and handler setup."""

import io
import json
import logging

import pytest
from app.core.config import SettingsError, load_settings
from app.core.logging import JsonFormatter, TextFormatter, configure_logging


def test_text_format_fields() -> None:
    """Text lines carry the UTC time, level, logger and request id."""
    record = logging.LogRecord(
        name="app.services.chat",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Created ticket %s",
        args=("TKT-1",),
        exc_info=None,
    )
    record.request_id = "abc123"
    line = TextFormatter().format(record)

    assert " INFO app.services.chat [req=abc123] Created ticket TKT-1" in line
    assert line.split()[0].endswith("Z")


def test_json_line_parses_and_is_utc() -> None:
    """A JSON line has the required fields and a UTC timestamp."""
    record = logging.LogRecord(
        name="app.services.chat",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc123"
    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.services.chat"
    assert payload["message"] == "hello"
    assert payload["request_id"] == "abc123"
    assert payload["timestamp"].endswith("Z")


def test_text_message_cannot_forge_a_second_line() -> None:
    """A newline inside the message stays on the same log line."""
    record = logging.LogRecord(
        name="app.services.chat",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="a\nINFO forged",
        args=(),
        exc_info=None,
    )
    record.request_id = "-"
    line = TextFormatter().format(record)

    assert "\n" not in line
    assert "\\n" in line


def _our_handlers() -> list[logging.Handler]:
    return [
        handler for handler in logging.getLogger().handlers if getattr(handler, "_lumen_oak", False)
    ]


def test_configure_logging_is_idempotent() -> None:
    """A second configure call does not add a second handler."""
    settings = load_settings()
    stream = io.StringIO()
    configure_logging(settings, stream=stream)
    before = _our_handlers()
    configure_logging(settings, stream=io.StringIO())
    after = _our_handlers()

    assert len(before) == 1
    assert len(after) == 1


def test_invalid_log_level_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unknown LOG_LEVEL fails when settings load."""
    monkeypatch.setenv("LOG_LEVEL", "LOUD")

    with pytest.raises(SettingsError, match="LOG_LEVEL"):
        load_settings()


def test_safe_dump_hides_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """The startup dump does not contain secret values."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-live-secret-value")
    monkeypatch.setenv("PINECONE_API_KEY", "pcsk_live_secret")
    dumped = load_settings().safe_dump()
    text = str(dumped)

    assert "sk-live-secret-value" not in text
    assert "pcsk_live_secret" not in text
    assert isinstance(load_settings().openai_api_key, object)


def test_log_sql_ignored_outside_local(monkeypatch: pytest.MonkeyPatch) -> None:
    """LOG_SQL is forced off when the process is not local."""
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("LOG_SQL", "true")

    assert load_settings().log_sql is False
