"""Mask card numbers, emails, postcodes and secrets before they are logged."""

import re

_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_POSTCODE = re.compile(
    r"\b(?:GIR ?0AA|[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2})\b",
    re.IGNORECASE,
)
_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:password|passwd|pwd|secret|token|api_key|apikey)\b\s*[=:]\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|\S+)"
)
_JSON_SECRET = re.compile(
    r"(?i)(\"(?:password|passwd|pwd|secret|token|api_key|apikey)\"\s*:\s*\")"
    r"[^\"]*"
    r"(\")"
)
_BEARER = re.compile(r"(?i)\bBearer\s+\S+")
_KEY_PREFIX = re.compile(r"\b(?:sk-|pcsk_)\S+")


def redact(text: str) -> str:
    """Mask card numbers, emails, postcodes and secrets in text."""
    masked = _BEARER.sub("[secret]", text)
    masked = _KEY_PREFIX.sub("[secret]", masked)
    masked = _JSON_SECRET.sub(r"\1[secret]\2", masked)
    masked = _ASSIGNMENT.sub(r"\1[secret]", masked)
    masked = _EMAIL.sub("[email]", masked)
    masked = _POSTCODE.sub("[postcode]", masked)
    return _CARD.sub("[card]", masked)
