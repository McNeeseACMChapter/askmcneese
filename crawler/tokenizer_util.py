"""Token utilities for chunking.

Uses ``tiktoken`` when available for accurate token boundaries, and falls back
to a simple whitespace word tokenizer so the pipeline still runs offline.
"""

from __future__ import annotations

try:
    import tiktoken

    _ENC = tiktoken.get_encoding("cl100k_base")
    _HAS_TIKTOKEN = True
except Exception:  # pragma: no cover - fallback path
    _ENC = None
    _HAS_TIKTOKEN = False


def encode(text: str) -> list:
    if _HAS_TIKTOKEN:
        return _ENC.encode(text)
    return text.split()


def decode(tokens: list) -> str:
    if _HAS_TIKTOKEN:
        return _ENC.decode(tokens)
    return " ".join(tokens)


def count_tokens(text: str) -> int:
    return len(encode(text))

