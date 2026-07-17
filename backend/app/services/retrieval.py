"""ChromaDB retrieval service.

Reads chunks from the same ChromaDB collection the crawler writes to.
Backend is READ-ONLY — never writes to ChromaDB.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv

from app.services.query_expansion import expand_query
from app.services.rerank import rerank_texts

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "crawler/chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "askmcneese_sources")
# top_k feeds the LLM: multi-category fact questions (freshman + transfer +
# graduate scholarship tables, or a full degree plan) need several chunks, so
# default to 6 rather than 3.
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "6"))
# How many candidates to pull per sub-query before merge + rerank. This is the
# recall net: it must be wide enough that fact-dense table chunks enter the pool
# for the reranker to promote. Sized for the post-backfill KB (~1300+ chunks).
RETRIEVAL_PER_QUERY_K = int(os.getenv("RETRIEVAL_PER_QUERY_K", "12"))


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source_url: str
    title: str
    category: str
    trust_tier: str
    score: float
    chunk_type: str = "prose"


def _get_collection():
    """Get the ChromaDB collection (read-only access)."""
    db_path = Path(__file__).resolve().parents[3] / CHROMA_DB_PATH
    if not db_path.exists():
        raise FileNotFoundError(
            f"ChromaDB not found at {db_path}. Run crawler ingest first."
        )
    client = chromadb.PersistentClient(path=str(db_path))
    return client.get_or_create_collection(name=CHROMA_COLLECTION)


def search_chunks(question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Backward-compatible entrypoint — delegates to :func:`retrieve`."""
    return retrieve(question, top_k=top_k)


def _query_one(collection, subquery: str, per_query_k: int) -> list[dict]:
    """Run one embedding query and return raw candidate dicts."""
    results = collection.query(
        query_texts=[subquery],
        n_results=per_query_k,
        include=["documents", "metadatas", "distances"],
    )
    if not results["ids"] or not results["ids"][0]:
        return []
    ids = results["ids"][0]
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []
    out = []
    for i, cid in enumerate(ids):
        out.append({
            "id": cid,
            "text": docs[i] if i < len(docs) else "",
            "meta": metas[i] if i < len(metas) else {},
            "distance": distances[i] if i < len(distances) else 1.0,
        })
    return out


def retrieve(question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Multi-query retrieval with expansion, merge/dedup, and reranking.

    Pipeline:
    1. Expand the question into focused sub-queries (query_expansion).
    2. Embed + retrieve candidates for each sub-query (Chroma default embeddings).
    3. Merge and deduplicate by chunk_id (keep the best embedding distance).
    4. Optional Perplexity embeddings re-score of the candidate pool.
    5. Heuristic/cross-encoder rerank against the ORIGINAL question.
    6. Return the blended top_k.
    """
    if top_k is None:
        top_k = RETRIEVAL_TOP_K
    if not question or not question.strip():
        return []

    try:
        collection = _get_collection()
    except FileNotFoundError:
        return []
    if collection.count() == 0:
        return []

    per_query_k = min(RETRIEVAL_PER_QUERY_K, collection.count())
    subqueries = expand_query(question) or [question]

    # Merge candidates across sub-queries, keeping the closest distance seen.
    merged: dict[str, dict] = {}
    for sq in subqueries:
        for cand in _query_one(collection, sq, per_query_k):
            existing = merged.get(cand["id"])
            if existing is None or cand["distance"] < existing["distance"]:
                merged[cand["id"]] = cand

    if not merged:
        return []

    candidates = list(merged.values())
    texts = [c["text"] for c in candidates]
    chunk_types = [c["meta"].get("chunk_type", "prose") for c in candidates]

    # Perplexity embedding similarity (optional) — scores aligned to candidate index
    pplx_scores: dict[int, float] = {}
    try:
        from app.services.perplexity_embeddings import embeddings_enabled, rank_by_embedding

        if embeddings_enabled():
            ranked_pplx = embed_texts_rank_sync(question, texts)
            for idx, score in ranked_pplx:
                pplx_scores[idx] = max(0.0, float(score))
    except Exception as e:
        print(f"Perplexity embed rerank skipped: {e}")

    # Rerank against the original question (not the sub-queries).
    ranked = rerank_texts(question, texts, chunk_types=chunk_types)

    chunks: list[RetrievedChunk] = []
    for idx, rerank_score in ranked[: max(top_k * 2, top_k)]:
        cand = candidates[idx]
        meta = cand["meta"]
        embed_score = max(0.0, 1.0 - cand["distance"])
        pplx = pplx_scores.get(idx, 0.0)
        if pplx > 0:
            # Blend: heuristic/cross-encoder + Chroma distance + Perplexity cosine
            final = round(0.55 * rerank_score + 0.20 * embed_score + 0.25 * pplx, 3)
        else:
            final = round(0.75 * rerank_score + 0.25 * embed_score, 3)
        chunks.append(
            RetrievedChunk(
                chunk_id=cand["id"],
                text=cand["text"],
                source_url=meta.get("source_url", ""),
                title=meta.get("title", "Unknown Source"),
                category=meta.get("category", ""),
                trust_tier=meta.get("trust_tier", ""),
                score=final,
                chunk_type=meta.get("chunk_type", "prose"),
            )
        )
    chunks.sort(key=lambda c: c.score, reverse=True)
    return chunks[:top_k]


def embed_texts_rank_sync(question: str, texts: list[str]) -> list[tuple[int, float]]:
    """Sync wrapper for Perplexity embedding rank (retrieval is sync today)."""
    import asyncio

    from app.services.perplexity_embeddings import rank_by_embedding

    try:
        return asyncio.run(rank_by_embedding(question, texts))
    except RuntimeError:
        # Nested event loop — skip rather than deadlock
        return []


def get_collection_stats() -> dict:
    """Get statistics about the ChromaDB collection."""
    try:
        collection = _get_collection()
        return {
            "collection": CHROMA_COLLECTION,
            "count": collection.count(),
            "path": str(Path(__file__).resolve().parents[3] / CHROMA_DB_PATH),
        }
    except FileNotFoundError as e:
        return {"error": str(e), "count": 0}
