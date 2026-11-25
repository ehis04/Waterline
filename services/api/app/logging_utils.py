"""Structured logging utilities with automatic secret and PII redaction."""

import logging
import re
from typing import Any

REDACTED = "[REDACTED]"

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "x-api-key",
        "token",
        "access_token",
        "refresh_token",
        "email",
        "account_number",
        "password",
        "secret",
    }
)

_AUTH_HEADER_RE = re.compile(
    r"(?i)(authorization\s*[:=]\s*)(?:bearer|basic|token)?\s*[A-Za-z0-9\-._~+/]+=*"
)
_KV_SECRET_RE = re.compile(
    r"(?i)\b(api_key|apikey|x-api-key|token|access_token|refresh_token|account_number|password|secret)"
    r"(\s*[:=]\s*)([^\s,;\"']+)"
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def redact_text(text: str) -> str:
    """Redact credentials, tokens, account numbers, and email addresses from freeform text."""
    if not text:
        return text
    masked = _AUTH_HEADER_RE.sub(rf"\1{REDACTED}", text)
    masked = _KV_SECRET_RE.sub(rf"\1\2{REDACTED}", masked)
    masked = _EMAIL_RE.sub(REDACTED, masked)
    return masked


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive keys and PII patterns in mappings, sequences, and strings."""
    if isinstance(data, dict):
        return {
            k: (REDACTED if str(k).lower() in SENSITIVE_KEYS else redact_sensitive_data(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(redact_sensitive_data(item) for item in data)
    if isinstance(data, str):
        return redact_text(data)
    return data


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secrets and PII from log messages, args, and extra fields."""

    _STANDARD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        elif isinstance(record.msg, (dict, list, tuple)):
            record.msg = redact_sensitive_data(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_sensitive_data(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_sensitive_data(arg) for arg in record.args)

        for attr in list(record.__dict__.keys()):
            if attr in self._STANDARD_ATTRS:
                continue
            if attr.lower() in SENSITIVE_KEYS:
                setattr(record, attr, REDACTED)
            else:
                setattr(record, attr, redact_sensitive_data(getattr(record, attr)))

        return True


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the waterline logger with RedactingFilter attached."""
    logger = logging.getLogger("waterline")
    logger.setLevel(level)
    if not any(isinstance(f, RedactingFilter) for f in logger.filters):
        logger.addFilter(RedactingFilter())
    for handler in logger.handlers:
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(RedactingFilter())
    return logger
