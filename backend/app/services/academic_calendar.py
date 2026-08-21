"""Term-aware routing helpers for McNeese academic schedule pages.

This module resolves *where* to look. It never stores or returns academic-date
answers. Dates must still be fetched from, extracted from, and cited to a live
official McNeese page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from zoneinfo import ZoneInfo


_TERM_RE = re.compile(
    r"\b(spring|summer|fall|winter)(?:\s+(?:semester|session|term))?(?:\s+(20\d{2}))?\b",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_FINAL_RE = re.compile(r"\bfinal(?:s|\s+exam(?:ination)?s?)?\b", re.IGNORECASE)

_SCHEDULE_BASE = (
    "https://www.mcneese.edu/about-us/leadership-team/administrative-and-student-affairs/"
    "division-of-administrative-and-student-affairs/student-central/registrar/schedule"
)


@dataclass(frozen=True)
class AcademicTermReference:
    term: str
    year: int
    explicit_year: bool

    @property
    def slug(self) -> str:
        return f"{self.term}-{self.year}"

    @property
    def label(self) -> str:
        return f"{self.term.title()} {self.year}"


def campus_today() -> date:
    """Return the calendar date used by McNeese, independent of server region."""
    from datetime import datetime

    return datetime.now(ZoneInfo("America/Chicago")).date()


def _inferred_year(term: str, today: date) -> int:
    """Resolve an unqualified term to its current or next useful occurrence.

    Fall belongs to the current calendar year. Spring and summer roll forward
    after their normal academic windows have passed. This makes phrases such as
    "our fall semester" deterministic without embedding any semester date.
    """
    if term == "spring":
        return today.year if today.month <= 5 else today.year + 1
    if term == "summer":
        return today.year if today.month <= 8 else today.year + 1
    if term == "winter":
        return today.year if today.month <= 2 else today.year + 1
    return today.year


def resolve_academic_term(
    question: str,
    *,
    today: date | None = None,
) -> AcademicTermReference | None:
    match = _TERM_RE.search(question or "")
    if not match:
        return None
    term = match.group(1).lower()
    year_match = match.group(2) or (_YEAR_RE.search(question or "").group(1) if _YEAR_RE.search(question or "") else None)
    if year_match:
        return AcademicTermReference(term=term, year=int(year_match), explicit_year=True)
    reference_day = today or campus_today()
    return AcademicTermReference(
        term=term,
        year=_inferred_year(term, reference_day),
        explicit_year=False,
    )


def academic_schedule_url_candidates(
    question: str,
    *,
    today: date | None = None,
) -> list[str]:
    """Return bounded official URL candidates for a term question.

    McNeese currently has both single- and double-``schedule`` CMS nesting in
    production. Both are tried because the authoritative content, not a guessed
    route, decides which candidate is valid.
    """
    reference = resolve_academic_term(question, today=today)
    if reference is None:
        return []

    slug = reference.slug
    term_pages = [
        f"{_SCHEDULE_BASE}/{slug}/",
        f"{_SCHEDULE_BASE}/schedule/{slug}/",
    ]
    wants_finals = bool(_FINAL_RE.search(question or ""))
    candidates: list[str] = []
    if wants_finals:
        candidates.extend(
            [
                f"{_SCHEDULE_BASE}/{slug}-final-exam-schedule/",
                f"{_SCHEDULE_BASE}/{slug}/{slug}-final-exam-schedule/",
                f"{_SCHEDULE_BASE}/schedule/{slug}-final-exam-schedule/",
                f"{_SCHEDULE_BASE}/schedule/{slug}/{slug}-final-exam-schedule/",
            ]
        )
    candidates.extend(term_pages)
    return list(dict.fromkeys(candidates))


def is_academic_schedule_candidate(
    url: str,
    question: str,
    *,
    title: str = "",
    today: date | None = None,
) -> bool:
    reference = resolve_academic_term(question, today=today)
    if reference is None:
        return False
    blob = f"{title} {url}".lower().replace("_", "-")
    if "mcneese.edu" not in blob or "/registrar/schedule" not in blob:
        return False
    if reference.slug not in blob and reference.label.lower() not in blob:
        return False
    wants_finals = bool(_FINAL_RE.search(question or ""))
    has_finals = "final" in blob and "exam" in blob
    return wants_finals or not has_finals
