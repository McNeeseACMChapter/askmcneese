"""BE-03 — Chunker v0.

Split clean text into ~300-token chunks with 50-token overlap and attach the
metadata required for future citations and freshness checks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import tokenizer_util

CHUNK_SIZE = 300
OVERLAP = 50


@dataclass
class Chunk:
    chunk_id: str
    chunk_index: int
    text: str
    source_url: str
    title: str
    category: str
    trust_tier: str
    last_checked_date: str


def chunk_text(
    text: str,
    *,
    source_url: str,
    title: str,
    category: str,
    trust_tier: str,
    last_checked_date: str,
    source_id: str = "SRC",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[Chunk]:
    tokens = tokenizer_util.encode(text)
    if not tokens:
        return []

    step = max(1, chunk_size - overlap)
    chunks: list[Chunk] = []
    index = 0
    for start in range(0, len(tokens), step):
        window = tokens[start:start + chunk_size]
        if not window:
            break
        chunk_str = tokenizer_util.decode(window).strip()
        if not chunk_str:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{source_id}-{index:04d}",
                chunk_index=index,
                text=chunk_str,
                source_url=source_url,
                title=title,
                category=category,
                trust_tier=trust_tier,
                last_checked_date=last_checked_date,
            )
        )
        index += 1
        if start + chunk_size >= len(tokens):
            break
    return chunks


def chunk_to_dict(chunk: Chunk) -> dict:
    return asdict(chunk)
