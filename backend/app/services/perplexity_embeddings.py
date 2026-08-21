"""Perplexity Embeddings API — query/chunk semantic scoring.

Uses https://api.perplexity.ai/v1/embeddings (pplx-embed-v1-*).
Does not replace Chroma storage embeddings; used to re-score candidates.
"""

from __future__ import annotations

import base64
import math
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ASK = _BACKEND_ROOT.parent
load_dotenv(_BACKEND_ROOT / ".env", override=False)
load_dotenv(_REPO_ASK / ".env", override=False)

from app.services.search_providers import perplexity_key


def embeddings_enabled() -> bool:
    return os.getenv("PERPLEXITY_EMBEDDINGS_ENABLED", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def embed_model() -> str:
    return (os.getenv("PERPLEXITY_EMBED_MODEL") or "pplx-embed-v1-0.6b").strip()


def embed_dimensions() -> int | None:
    raw = (os.getenv("PERPLEXITY_EMBED_DIMENSIONS") or "").strip()
    if not raw:
        return 1024 if "0.6b" in embed_model() else None
    try:
        return int(raw)
    except ValueError:
        return None


def _decode_embedding(value: object) -> list[float]:
    """Decode Perplexity embedding (float list or base64 int8/binary)."""
    if isinstance(value, list):
        return [float(x) for x in value]
    if not isinstance(value, str):
        return []
    # Prefer treating as base64 int8 (API default)
    try:
        raw = base64.b64decode(value)
        # signed int8
        ints = [b if b < 128 else b - 256 for b in raw]
        return [float(x) for x in ints]
    except Exception:
        return []


def _l2_normalize(vec: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    # Embeddings are unnormalized — normalize then dot
    an = _l2_normalize(a)
    bn = _l2_normalize(b)
    return sum(x * y for x, y in zip(an, bn))


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed one or more texts. Returns vectors aligned with input order."""
    key = perplexity_key()
    if not key or not texts:
        return []
    cleaned = [(t or " ").strip() or " " for t in texts]
    payload: dict = {
        "model": embed_model(),
        "input": cleaned if len(cleaned) > 1 else cleaned[0],
    }
    dims = embed_dimensions()
    if dims:
        payload["dimensions"] = dims
    # Prefer float-compatible path when API accepts it; fall back handled by decode
    payload["encoding_format"] = os.getenv("PERPLEXITY_EMBED_ENCODING", "float")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.post(
            "https://api.perplexity.ai/v1/embeddings",
            headers=headers,
            json=payload,
        )
        if r.status_code >= 400 and payload.get("encoding_format") == "float":
            # Older/newer accounts may only support base64_int8
            payload["encoding_format"] = "base64_int8"
            r = await client.post(
                "https://api.perplexity.ai/v1/embeddings",
                headers=headers,
                json=payload,
            )
        r.raise_for_status()
        data = r.json()

    items = data.get("data") or []
    # Ensure order by index
    items = sorted(items, key=lambda x: int(x.get("index", 0)))
    out: list[list[float]] = []
    for item in items:
        out.append(_decode_embedding(item.get("embedding")))
    return out


def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Caller should use async path; fall back to new loop in thread is messy —
        # run blocking httpx via asyncio.run in a fresh context only when safe.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(embed_texts(texts))).result()
    return asyncio.run(embed_texts(texts))


async def rank_by_embedding(
    query: str,
    documents: list[str],
    *,
    top_k: int | None = None,
) -> list[tuple[int, float]]:
    """Return (index, cosine_score) sorted desc for document texts."""
    if not embeddings_enabled() or not perplexity_key() or not documents:
        return [(i, 0.0) for i in range(len(documents))]
    try:
        vectors = await embed_texts([query] + list(documents))
    except Exception as e:
        print(f"Perplexity embeddings failed: {e}")
        return [(i, 0.0) for i in range(len(documents))]
    if len(vectors) < 2:
        return [(i, 0.0) for i in range(len(documents))]
    qv = vectors[0]
    scored: list[tuple[int, float]] = []
    for i, dv in enumerate(vectors[1:]):
        scored.append((i, cosine_similarity(qv, dv)))
    scored.sort(key=lambda x: x[1], reverse=True)
    if top_k is not None:
        scored = scored[:top_k]
    return scored
