"""Application logging. One stdout handler, with redaction and a request id."""

import json
import logging
import sys
import time
from collections.abc import Mapping
from typing import IO, Any

from app.core.config import Settings
from app.core.redaction import redact
from app.core.request_context import get_request_id

_CONFIGURED = False
_HANDLER_MARK = "_lumen_oak"
_QUIET_LOGGERS = ("httpx", "httpcore", "urllib3", "openai", "pinecone")
_STANDARD_ATTRS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def configure_logging(settings: Settings, *, stream: IO[str] | None = None) -> None:
    """Attach one stdout handler. A second call does not add another handler."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(stream or sys.stdout)
    setattr(handler, _HANDLER_MARK, True)
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers = [item for item in root.handlers if not getattr(item, _HANDLER_MARK, False)]
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.propagate = False
    access.disabled = True

    _CONFIGURED = True
    logging.getLogger(__name__).info(
        "Starting env=%s level=%s settings=%s",
        settings.app_env,
        settings.log_level,
        settings.safe_dump(),
    )


class RequestIdFilter(logging.Filter):
    """Copy the current request id onto each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach `request_id` before the record is formatted."""
        record.request_id = get_request_id()
        return True


class TextFormatter(logging.Formatter):
    """One text line: time, level, logger, request id, redacted message."""

    def __init__(self) -> None:
        """Use UTC timestamps."""
        super().__init__(
            fmt="%(asctime)s %(levelname)s %(name)s [req=%(request_id)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        self.converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        """Redact the message and keep traceback newlines."""
        message = _escape_controls(redact(record.getMessage()))
        extras = _redact_extra(record)
        if extras:
            message = f"{message} {_format_extra(extras)}"
        line = (
            f"{self.formatTime(record, self.datefmt)} {record.levelname} "
            f"{record.name} [req={getattr(record, 'request_id', '-')}] {message}"
        )
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            line = f"{line}\n{redact(record.exc_text)}"
        return line


class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Redact message, extra fields and the traceback."""
        payload: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
            "request_id": getattr(record, "request_id", "-"),
        }
        payload.update(_redact_extra(record))
        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def _escape_controls(text: str) -> str:
    return text.replace("\r", "\\r").replace("\n", "\\n")


def _redact_extra(record: logging.LogRecord) -> dict[str, Any]:
    extras: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key in _STANDARD_ATTRS or key == "request_id":
            continue
        extras[key] = _redact_value(value)
    return extras


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, Mapping):
        return {str(key): _redact_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        redacted = [_redact_value(item) for item in value]
        return redacted if isinstance(value, list) else tuple(redacted)
    return value


def _format_extra(extras: Mapping[str, Any]) -> str:
    return " ".join(f"{key}={value}" for key, value in extras.items())
