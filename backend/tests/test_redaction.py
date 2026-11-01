"""Redaction covers messages, arguments, extra fields and tracebacks."""

import logging
import sys

from app.core.logging import JsonFormatter
from app.core.redaction import redact


def test_cards_emails_postcodes_and_secrets() -> None:
    """Known sensitive shapes are replaced and business identifiers are kept."""
    text = redact(
        "4111 1111 1111 1111 4111111111111111 4111-1111-1111-1111 "
        "ada@lumen.test SW1A 1AA te1 1st password=Hunter2! "
        '{"password": "Hunter2!"} Bearer abc.def sk-testkey pcsk_testkey '
        "LO-900001 RMA-100 TKT-9 £12.95 2026-10-27 customer_id=12"
    )

    assert "4111" not in text
    assert "[card]" in text
    assert "ada@lumen.test" not in text
    assert "[email]" in text
    assert "SW1A" not in text.upper()
    assert "te1 1st" not in text.lower()
    assert "[postcode]" in text
    assert "Hunter2!" not in text
    assert "[secret]" in text
    assert "abc.def" not in text
    assert "sk-testkey" not in text
    assert "pcsk_testkey" not in text
    assert "LO-900001" in text
    assert "RMA-100" in text
    assert "TKT-9" in text
    assert "£12.95" in text
    assert "2026-10-27" in text
    assert "customer_id=12" in text


def test_redact_is_idempotent() -> None:
    """A second pass does not change the masked text."""
    original = "ada@lumen.test password=Hunter2! 4111111111111111"
    once = redact(original)

    assert redact(once) == once


def test_redaction_covers_arguments_extra_and_traceback() -> None:
    """Secrets in arguments, nested extra fields and tracebacks are masked."""
    try:
        raise RuntimeError("token=Hunter2! ada@lumen.test")
    except RuntimeError:
        record = logging.LogRecord(
            name="app.services.chat",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="failed %s",
            args=("sk-secretkey",),
            exc_info=sys.exc_info(),
        )
    record.request_id = "-"
    record.nested = {"email": "ada@lumen.test"}
    line = JsonFormatter().format(record)

    assert "sk-secretkey" not in line
    assert "Hunter2!" not in line
    assert "ada@lumen.test" not in line
    assert "[secret]" in line
    assert "[email]" in line
