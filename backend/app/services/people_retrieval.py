"""Exact public McNeese directory lookup for faculty and staff."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from app.services.rccs.models import RetrievedEvidence, utcnow
from app.services.web_search import _fetch_http_html


FACULTY_DIRECTORY_URL = "https://www.mcneese.edu/faculty/"


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _matching_directory_block(html: str, person_name: str) -> str | None:
    """Return the smallest useful directory block containing the exact name."""
    target = _clean(person_name).casefold()
    if not target:
        return None
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[Tag] = []
    for node in soup.find_all(["a", "h2", "h3", "h4", "strong"]):
        if target in _clean(node.get_text(" ", strip=True)).casefold():
            candidates.append(node)
    for node in candidates:
        current: Tag | None = node
        for _ in range(6):
            if current is None:
                break
            text = _clean(current.get_text(" ", strip=True))
            if target in text.casefold() and 20 <= len(text) <= 1400:
                has_directory_detail = bool(
                    re.search(r"(?:@mcneese\.edu|\b\d{3}[-.) ]\d{3}[- ]\d{4}\b|\boffice\b|\bdepartment\b)", text, re.I)
                )
                if has_directory_detail:
                    return text
            parent = current.parent
            current = parent if isinstance(parent, Tag) else None
    return None


async def retrieve_person_directory(person_name: str) -> RetrievedEvidence | None:
    """Fetch and parse the public directory without relying on a 10k page prefix."""
    try:
        final_url, html, error = await _fetch_http_html(FACULTY_DIRECTORY_URL)
    except Exception:
        return None
    if error or not html:
        return None
    block = _matching_directory_block(html, person_name)
    if not block:
        return None
    return RetrievedEvidence(
        evidence_id=f"ev-directory-{abs(hash(person_name.casefold())) % 10_000_000}",
        title=f"McNeese faculty and staff directory — {person_name}",
        url=final_url or FACULTY_DIRECTORY_URL,
        text=block,
        source_id="MCNEESE_DIRECTORY",
        source_name="McNeese faculty and staff directory",
        source_tier="A",
        trust_level="official",
        category="person_directory",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.98,
        entity_match_score=1.0,
        metadata={"citation_label": "Official McNeese directory", "matched_name": person_name},
    )
