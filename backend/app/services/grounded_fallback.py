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


_REGISTRY_STUB = "Governed campus source record"


def _content_bearing_chunks(destinations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer fetched page text over registry destination stubs."""
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for chunk in destinations:
        if chunk.get("is_link_only"):
            continue
        text = str(chunk.get("text") or "").strip()
        if len(text) < 80 or _REGISTRY_STUB in text:
            continue
        meta = chunk.get("metadata") or {}
        bonus = 0
        if meta.get("page_read") or meta.get("page_fetched"):
            bonus += 3
        if str(chunk.get("retrieval_channel") or "") in {"official_live", "page_open", "kb"}:
            bonus += 1
        scored.append((bonus, len(text), chunk))
    scored.sort(key=lambda item: (-item[0], -item[1]))
    return [chunk for _, _, chunk in scored]


def _excerpt_official_text(chunk: dict[str, Any], question: str = "") -> str:
    excerpt = re.sub(
        r"(?:\n|^)Relevant official action links found on this page:.*\Z",
        "",
        str(chunk.get("text") or ""),
        flags=re.I | re.S,
    ).strip()
    excerpt = re.sub(r"\n{3,}", "\n\n", excerpt)
    asked = (question or "").lower()
    if re.search(r"\b(?:start|begin|first day)\b", asked) and not re.search(
        r"\b(?:deadline|withdraw|drop|last day)\b", asked
    ):
        match = re.search(
            r"\b(?:classes?\s+begin|instruction\s+begins?|semester\s+starts?|first\s+day)\b",
            excerpt,
            re.I,
        )
        if match:
            excerpt = excerpt[max(0, match.start() - 80) :]
    return excerpt[:1600].strip()


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

    readable = _content_bearing_chunks(destinations)
    if readable:
        source = readable[0]
        excerpt = _excerpt_official_text(source, question)
        link = _safe_link(str(source.get("title") or "Official source"), str(source["source_url"]))
        if excerpt:
            return (
                f"From the official page {link}:\n\n{excerpt}\n\n"
                "Open that source for the full official instructions."
            )

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

    if domain == "employment":
        links = "\n".join(
            f"- {_safe_link(str(chunk.get('title') or 'Official employment portal'), str(chunk['source_url']))}"
            for chunk in destinations[:4]
        )
        return (
            "I could not verify active position titles from the official listings within this request, "
            "so I will not invent vacancies. Check these verified McNeese employment destinations:\n\n"
            f"{links}"
        )

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
