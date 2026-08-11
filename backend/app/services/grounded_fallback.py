"""Deterministic, evidence-only fallback when answer synthesis is unavailable."""

from __future__ import annotations

import re
from typing import Any, Iterable


def _safe_link(title: str, url: str) -> str:
    label = re.sub(r"[\[\]\r\n]+", " ", title or "Official source").strip()
    return f"[{label}]({url})"


def _destinations(chunks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk in chunks:
        url = str(chunk.get("source_url") or "").strip()
        if not url.lower().startswith(("https://", "http://")):
            continue
        key = url.lower().rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        found.append(chunk)
    return found


def render_grounded_fallback(
    question: str,
    chunks: Iterable[dict[str, Any]],
    safe_response: dict[str, Any] | None = None,
) -> str:
    """Return a useful answer using only already-approved evidence.

    This is deliberately conservative: it can route to a verified destination
    or expose possible live matches, but never invents availability or policy.
    """
    destinations = _destinations(chunks)
    if not destinations:
        return "I could not verify enough approved McNeese evidence to answer reliably."

    safe = safe_response or {}
    compiled = safe.get("campus_query") or {}
    domain = str(compiled.get("domain") or "")
    subdomain = str(compiled.get("subdomain") or "")
    entities = compiled.get("entities") or {}

    if domain == "student_services" and subdomain == "bookstore":
        requested = str(entities.get("item") or "").strip()
        live_matches = [
            chunk
            for chunk in destinations
            if str(chunk.get("retrieval_channel") or "") == "web_live"
        ][:3]
        if live_matches:
            links = ", ".join(
                _safe_link(str(chunk.get("title") or "Possible listing"), str(chunk["source_url"]))
                for chunk in live_matches
            )
            subject = f" for **{requested}**" if requested else ""
            return (
                f"I found possible current matches{subject}: {links}. "
                "Check the author or ISBN before buying, because similar titles may refer to different books."
            )

        store = next(
            (
                chunk
                for chunk in destinations
                if "cowboy store" in str(chunk.get("title") or "").lower()
            ),
            destinations[0],
        )
        store_link = _safe_link(
            str(store.get("title") or "McNeese Cowboy Store"),
            str(store["source_url"]),
        )
        if requested:
            return (
                f"I could not confirm a current listing for **{requested}**. "
                f"Check the {store_link}; if it is not the book you mean, send the author or ISBN and I can narrow the search."
            )
        return f"Check current textbook and merchandise availability at the {store_link}."

    first = destinations[0]
    return (
        "I could not complete a full synthesis, but I did verify the relevant destination: "
        f"{_safe_link(str(first.get('title') or 'Official source'), str(first['source_url']))}."
    )


def direct_navigation_answer(
    question: str,
    chunks: Iterable[dict[str, Any]],
    safe_response: dict[str, Any] | None = None,
) -> str | None:
    """Finish destination-only navigation without paying for LLM synthesis."""
    materialized = list(chunks)
    compiled = (safe_response or {}).get("campus_query") or {}
    if str(compiled.get("action") or "") != "navigate" or not materialized:
        return None
    if not all(bool(chunk.get("is_link_only")) for chunk in materialized):
        return None
    return render_grounded_fallback(question, materialized, safe_response)
