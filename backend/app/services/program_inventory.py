"""Live undergraduate program inventory from McNeese Academics.

Fetches the official Undergraduate Programs directory via its WordPress AJAX
endpoint, collects program titles, and returns countable evidence for
"how many majors" / "what majors are offered" questions.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from html import unescape

import httpx

from app.services.rccs.evidence import sanitize_evidence_text
from app.services.rccs.models import RetrievedEvidence, utcnow

UNDERGRAD_PROGRAMS_URL = "https://www.mcneese.edu/academics/undergraduate-programs/"
_UA = {"User-Agent": "AskMcNeese/1.0 (+https://www.mcneese.edu)"}
_CACHE_TTL_SECONDS = 30 * 60
_cache: tuple[float, list[str], int] | None = None


def is_program_inventory_question(question: str) -> bool:
    q = (question or "").lower()
    asks_inventory = bool(
        re.search(
            r"\b(?:how many|number of|list(?: of)?|what(?: are)?|which|"
            r"available|offer(?:s|ed)?|majors? (?:does|do)|programs? (?:does|do))\b",
            q,
        )
    )
    asks_programs = bool(
        re.search(r"\b(?:majors?|undergraduate programs?|bachelor(?:'s)? programs?)\b", q)
    )
    named_curriculum = bool(
        re.search(
            r"\b(?:degree plan|curriculum|required courses?|course list|"
            r"what courses|classes (?:do i|should i))\b",
            q,
        )
    )
    return asks_inventory and asks_programs and not named_curriculum


def _extract_titles(html: str) -> list[str]:
    titles: list[str] = []
    for match in re.finditer(
        r'class="mcneese-program-card__title"[^>]*>(.*?)</',
        html or "",
        re.I | re.S,
    ):
        title = re.sub(r"<[^>]+>", "", unescape(match.group(1)))
        title = re.sub(r"\s+", " ", title).strip()
        if title:
            titles.append(title)
    return titles


def _load_ajax_config(html: str) -> dict:
    match = re.search(r"data-config=(['\"])(.*?)\1", html, re.S)
    if match:
        raw = unescape(match.group(2))
    else:
        match = re.search(r"data-config=&quot;(.*?)&quot;", html, re.S)
        if not match:
            raise RuntimeError("undergraduate_programs_config_missing")
        raw = unescape(match.group(1))
    return json.loads(raw)


def _unique(titles: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for title in titles:
        key = title.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(title)
    return out


def _split_majors_and_certificates(titles: list[str]) -> tuple[list[str], list[str]]:
    majors: list[str] = []
    certificates: list[str] = []
    for title in titles:
        if re.search(r"\bPBC\b|post[- ]baccalaureate|certificate\b", title, re.I):
            certificates.append(title)
        else:
            majors.append(title)
    return majors, certificates


def _fetch_undergraduate_titles_sync() -> tuple[list[str], int]:
    global _cache
    now = time.monotonic()
    if _cache and now - _cache[0] < _CACHE_TTL_SECONDS:
        return list(_cache[1]), _cache[2]

    with httpx.Client(timeout=30.0, follow_redirects=True, headers=_UA) as client:
        page = client.get(UNDERGRAD_PROGRAMS_URL)
        page.raise_for_status()
        config = _load_ajax_config(page.text)
        ajax_url = str(config.get("ajaxUrl") or "").strip()
        nonce = str(config.get("nonce") or "").strip()
        atts = dict(config.get("atts") or {})
        if not ajax_url or not nonce:
            raise RuntimeError("undergraduate_programs_ajax_incomplete")

        atts["type"] = "undergraduate"
        atts["per_page"] = max(int(atts.get("per_page") or 12), 100)
        titles: list[str] = []
        found_meta = 0
        paged = 1
        while paged <= 20:
            form = {
                "action": "mcneese_filter_programs",
                "nonce": nonce,
                "search": "",
                "paged": str(paged),
                "type": "undergraduate",
                "college": "",
                "category": "",
                "tag": "",
                "interest": "",
                "orderby": str(atts.get("orderby") or "title"),
                "order": str(atts.get("order") or "ASC"),
            }
            for key, value in atts.items():
                form[f"atts[{key}]"] = str(value)
            response = client.post(ajax_url, data=form)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("success"):
                raise RuntimeError("undergraduate_programs_ajax_failed")
            data = payload.get("data") or {}
            found_meta = int(data.get("found") or found_meta or 0)
            page_titles = _extract_titles(str(data.get("html") or ""))
            if not page_titles:
                break
            titles.extend(page_titles)
            max_pages = int(data.get("maxPages") or 1)
            if paged >= max_pages:
                break
            paged += 1

    unique = _unique(titles)
    found = found_meta or len(unique)
    _cache = (time.monotonic(), unique, found)
    return list(unique), found


async def retrieve_undergraduate_program_inventory(
    question: str,
) -> tuple[list[RetrievedEvidence], str | None]:
    """Return one evidence item with counted undergraduate majors/programs."""
    if not is_program_inventory_question(question):
        return [], None
    try:
        titles, found = await asyncio.to_thread(_fetch_undergraduate_titles_sync)
    except Exception as exc:
        return [], f"program_inventory_failed:{type(exc).__name__}"
    if not titles:
        return [], "program_inventory_empty"

    majors, certificates = _split_majors_and_certificates(titles)
    major_count = len(majors) if majors else len(titles)
    lines = [
        "Official McNeese Undergraduate Programs directory inventory.",
        f"Directory filter: Undergraduate.",
        f"Programs found on page metadata: {found}.",
        f"Undergraduate majors counted from titles: {major_count}.",
        f"Post-baccalaureate / certificate entries in the same directory: {len(certificates)}.",
        "",
        "Undergraduate major titles:",
    ]
    for title in majors or titles:
        lines.append(f"- {title}")
    if certificates:
        lines.append("")
        lines.append("Certificate / PBC titles in the undergraduate directory:")
        for title in certificates:
            lines.append(f"- {title}")

    text = sanitize_evidence_text("\n".join(lines), 12_000)
    evidence = RetrievedEvidence(
        evidence_id=f"ev-ug-programs-{major_count}",
        title=f"Undergraduate Programs — {major_count} majors",
        url=UNDERGRAD_PROGRAMS_URL,
        text=text,
        source_id="SRC-007",
        source_name="McNeese Undergraduate Programs",
        source_tier="A",
        trust_level="official",
        category="program_inventory",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.99,
        metadata={
            "citation_label": "Official undergraduate programs directory",
            "program_count": found,
            "major_count": major_count,
            "certificate_count": len(certificates),
            "major_titles": majors or titles,
            "page_read": True,
        },
    )
    return [evidence], None
