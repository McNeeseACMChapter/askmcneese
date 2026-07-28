"""LLM query rewrite before retrieval / web browse.

Produces a cleaner search query + focused sub-queries for embeddings and providers.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from app.services.llm import CLAUDE_MODEL, _extract_text_blocks, _get_client
from app.services.safe_errors import redact_sensitive


@dataclass
class RewrittenQuery:
    original: str
    rewritten: str
    subqueries: list[str] = field(default_factory=list)
    provider: str = "none"

    @property
    def primary(self) -> str:
        return (self.rewritten or self.original or "").strip()


def rewrite_enabled() -> bool:
    return os.getenv("QUERY_REWRITE_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def should_rewrite_question(
    question: str,
    *,
    use_web_search: bool = False,
    classification_confidence: float = 1.0,
    secondary_intents: int = 0,
) -> bool:
    """Rewrite only structurally difficult queries, never every ordinary turn.

    This is routing, not a canned-answer shortcut: every answer still uses retrieval.
    """
    if not rewrite_enabled():
        return False
    if os.getenv("QUERY_REWRITE_FORCE", "0") == "1":
        return True

    q = re.sub(r"\s+", " ", (question or "").strip())
    words = re.findall(r"\b[\w'-]+\b", q)
    sentence_count = len(re.findall(r"[?!]", q))
    vague_reference = bool(
        re.search(r"\b(?:it|that|this|they|them|those|the above|same one)\b", q, re.I)
    )

    if classification_confidence < 0.55:
        return True
    if vague_reference and len(words) <= 14:
        return True
    if secondary_intents >= 2:
        return True
    if len(words) >= 34 or (sentence_count >= 2 and len(words) >= 20):
        return True
    if use_web_search and len(words) >= 26:
        return True
    return False

def rewrite_question(question: str, *, use_web_search: bool = False) -> RewrittenQuery:
    """Rewrite the user question into a retrieval-ready form via Claude."""
    q = (question or "").strip()
    if not q:
        return RewrittenQuery(original="", rewritten="", subqueries=[])
    if not rewrite_enabled():
        return RewrittenQuery(original=q, rewritten=q, subqueries=[q], provider="off")

    mode = "live web + knowledge retrieval" if use_web_search else "McNeese knowledge-base retrieval"
    prompt = (
        f"Rewrite the user's campus question for {mode}.\n"
        "Return EXACTLY this format (no markdown):\n"
        "REWRITTEN: <one clear search-ready question mentioning McNeese when relevant>\n"
        "SUBQUERY: <focused sub-query 1>\n"
        "SUBQUERY: <focused sub-query 2>\n"
        "SUBQUERY: <optional sub-query 3>\n"
        "Rules: keep named people/orgs; expand vague pronouns; do not invent facts; "
        "for ratings include Rate My Professors; for orgs include presence.io when relevant.\n\n"
        f"Question: {q}"
    )
    try:
        client = _get_client()
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=280,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _extract_text_blocks(list(resp.content or []))
        rewritten = q
        subs: list[str] = []
        for line in raw.splitlines():
            s = line.strip()
            if s.upper().startswith("REWRITTEN:"):
                rewritten = s.split(":", 1)[1].strip() or q
            elif s.upper().startswith("SUBQUERY:"):
                sq = s.split(":", 1)[1].strip()
                if sq:
                    subs.append(sq)
        if not subs:
            # Fallback: split non-empty lines
            for line in raw.splitlines():
                ln = re.sub(r"^\s*[-*\d.]+\s*", "", line).strip()
                if ln and not ln.upper().startswith("REWRITTEN"):
                    subs.append(ln)
        ordered: list[str] = []
        for item in [rewritten, *subs, q]:
            key = re.sub(r"\s+", " ", item.lower()).strip()
            if key and key not in {re.sub(r"\s+", " ", x.lower()) for x in ordered}:
                ordered.append(item.strip())
        return RewrittenQuery(
            original=q,
            rewritten=rewritten,
            subqueries=ordered[:5],
            provider="claude",
        )
    except Exception as e:
        print(f"Query rewrite failed: {redact_sensitive(e)}")
        return RewrittenQuery(original=q, rewritten=q, subqueries=[q], provider="fallback")
