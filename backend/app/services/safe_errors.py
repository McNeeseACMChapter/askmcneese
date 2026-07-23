"""Redact secrets and keep operational errors safe for logs and clients."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SECRET_QUERY_KEYS = {
    "api_key",
    "apikey",
    "key",
    "token",
    "access_token",
    "auth",
    "authorization",
    "secret",
}
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|token|access[_-]?token|authorization|secret)"
    r"(\s*[:=]\s*)([^\s,;&]+)"
)
_PROVIDER_KEY = re.compile(r"\b(?:sk-ant-|pplx-|tvly-)[A-Za-z0-9._-]{8,}")


def _redact_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        if not parts.scheme or not parts.netloc:
            return value
        query = [
            (key, "[REDACTED]" if key.lower() in _SECRET_QUERY_KEYS else item)
            for key, item in parse_qsl(parts.query, keep_blank_values=True)
        ]
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )
    except Exception:
        return value


def redact_sensitive(value: object, *, max_length: int = 600) -> str:
    """Return a bounded error string with credential-shaped values removed."""
    text = str(value or "")
    for candidate in re.findall(r"https?://[^\s'\"<>]+", text):
        text = text.replace(candidate, _redact_url(candidate))
    text = _SECRET_ASSIGNMENT.sub(r"\1\2[REDACTED]", text)
    text = _PROVIDER_KEY.sub("[REDACTED]", text)
    text = text.replace("\r", " ").replace("\n", " ")
    return text[:max_length]


def public_error_message(_error: object) -> str:
    """Stable client-facing message; details remain in redacted server logs."""
    return "The request could not be completed. Please try again."
