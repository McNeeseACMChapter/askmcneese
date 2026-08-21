"""Reranking — reorder merged retrieval candidates by true query relevance.

Embedding similarity alone is coarse: it returns a blurry neighborhood and can't
tell that a chunk literally containing "GPA 3.0" and "$1000" answers a scholarship
question better than a generic overview paragraph. After query expansion produces
a merged candidate pool, we rerank it before generation.

Backends (auto-selected, override with ``RERANK_METHOD``):
- ``cross_encoder``: sentence-transformers CrossEncoder (best quality, optional dep)
- ``llm``: Anthropic relevance scoring (uses existing client; adds latency)
- ``heuristic`` (always-available fallback): lexical overlap + phrase hits +
  concrete-fact density (numbers, money, dates, GPA) + structured-chunk bonus.

The reranker returns ``(original_index, score)`` pairs sorted best-first so callers
can reorder their own objects without this module knowing their shape.
"""

from __future__ import annotations

import os
import re

RERANK_METHOD = os.getenv("RERANK_METHOD", "auto").strip().lower()

_STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "to", "in", "on", "at", "for", "and",
    "or", "what", "when", "where", "which", "who", "how", "do", "does", "did",
    "can", "i", "you", "me", "my", "we", "it", "that", "this", "with", "about",
    "from", "as", "be", "will", "would", "should", "could", "have", "has",
    "get", "got", "there", "please", "tell", "give", "want", "need", "know",
    "mcneese", "university", "state",
}

_MONEY = re.compile(r"\$\s?\d")
_GPA = re.compile(r"\b\d\.\d{1,2}\b")
_MONTHS = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\b", re.I,
)
_NUM = re.compile(r"\b\d{2,}\b")

_cross_encoder = None
_cross_encoder_failed = False


def _keywords(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9'+.]+", text.lower())
            if len(w) > 2 and w not in _STOPWORDS]


def _heuristic_score(query: str, text: str, chunk_type: str = "prose") -> float:
    if not text:
        return 0.0
    q_low = query.lower()
    t_low = text.lower()
    q_terms = set(_keywords(query))
    if not q_terms:
        return 0.0

    # Lexical coverage: fraction of unique query terms present.
    hits = sum(1 for kw in q_terms if kw in t_low)
    coverage = hits / len(q_terms)

    # Phrase bonus: contiguous 2-grams from the query appearing verbatim.
    q_words = [w for w in re.findall(r"[a-z0-9']+", q_low) if w not in _STOPWORDS]
    bigrams = {f"{a} {b}" for a, b in zip(q_words, q_words[1:])}
    phrase_bonus = 0.1 * sum(1 for bg in bigrams if bg in t_low)

    # Concrete-fact density — the stuff good answers lead with.
    fact_bonus = 0.0
    if _MONEY.search(text):
        fact_bonus += 0.15
    if _GPA.search(text):
        fact_bonus += 0.1
    if _MONTHS.search(text):
        fact_bonus += 0.1
    if _NUM.search(text):
        fact_bonus += 0.05

    # Structured chunks (tables/lists) usually hold the tiered facts.
    structure_bonus = 0.15 if chunk_type in ("table", "list") else 0.0

    score = coverage + phrase_bonus + fact_bonus + structure_bonus
    return min(score, 2.0)


def _cross_encoder_scores(query: str, texts: list[str]) -> list[float] | None:
    global _cross_encoder, _cross_encoder_failed
    if _cross_encoder_failed:
        return None
    try:
        if _cross_encoder is None:
            from sentence_transformers import CrossEncoder
            model_name = os.getenv(
                "RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
            )
            _cross_encoder = CrossEncoder(model_name)
        scores = _cross_encoder.predict([[query, t] for t in texts])
        return [float(s) for s in scores]
    except Exception:
        _cross_encoder_failed = True
        return None


def _llm_scores(query: str, texts: list[str]) -> list[float] | None:
    try:
        import json

        from app.services.llm import _get_client, CLAUDE_MODEL

        client = _get_client()
        passages = "\n\n".join(
            f"[{i}] {t[:600]}" for i, t in enumerate(texts)
        )
        prompt = (
            "Score how well each passage answers the question on a 0-10 scale. "
            'Return ONLY a JSON object mapping the passage index to its score, e.g. '
            '{"0": 8, "1": 3}.\n\n'
            f"Question: {query}\n\nPassages:\n{passages}"
        )
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text if resp.content else "{}"
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
        return [float(data.get(str(i), 0.0)) for i in range(len(texts))]
    except Exception:
        return None


def rerank_texts(
    query: str,
    texts: list[str],
    *,
    top_n: int | None = None,
    chunk_types: list[str] | None = None,
    method: str | None = None,
) -> list[tuple[int, float]]:
    """Return ``(original_index, score)`` sorted best-first.

    Always falls back to the heuristic so this never raises and always works
    offline (important for CI / the eval harness).
    """
    if not texts:
        return []

    method = (method or RERANK_METHOD).lower()
    scores: list[float] | None = None

    if method in ("auto", "cross_encoder"):
        scores = _cross_encoder_scores(query, texts)
    if scores is None and method == "llm":
        scores = _llm_scores(query, texts)

    if scores is None:
        types = chunk_types or ["prose"] * len(texts)
        scores = [
            _heuristic_score(query, t, types[i] if i < len(types) else "prose")
            for i, t in enumerate(texts)
        ]

    ranked = sorted(enumerate(scores), key=lambda x: -x[1])
    return ranked[:top_n] if top_n else ranked
