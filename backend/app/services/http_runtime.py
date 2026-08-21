"""Shared HTTP runtime primitives for low-latency async retrieval."""

from __future__ import annotations

import ssl
from functools import lru_cache


@lru_cache(maxsize=1)
def shared_ssl_context() -> ssl.SSLContext:
    """Load the operating-system certificate store once per backend process."""
    return ssl.create_default_context()
