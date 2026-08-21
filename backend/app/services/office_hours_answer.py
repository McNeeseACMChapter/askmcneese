"""Grounded deterministic office-hours answers for campus directory requests."""

from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.office_hours import (
    calculate_office_status,
    format_clock,
    format_duration,
    parse_weekly_hours,
    regular_hours_for_day,
)


_STOP = {
    "and", "are", "can", "department", "does", "for", "how", "hours", "is",
    "mcneese", "office", "open", "close", "the", "time", "today", "what",
    "when", "where", "which", "who",
}
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?337\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@mcneese\.edu\b", re.I)
_ADDRESS_RE = re.compile(
    r"\b\d{3,5}\s+[A-Z][A-Za-z0-9 .'-]{1,70}?(?:Street|St\.?|Road|Rd\.?|Drive|Dr\.?|Avenue|Ave\.?)\b"
)


def _terms(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 2 and token not in _STOP
    }


def _source_for_question(question: str, chunks: list[dict]) -> tuple[dict, list] | None:
    question_terms = _terms(question)
    if not question_terms:
        # A bare "office hours" request does not identify an owner. Choosing
        # the first hours-bearing chunk would silently transfer another
        # department's schedule.
        return None
    candidates: list[tuple[int, dict, list]] = []
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        if not (metadata.get("page_fetched") or metadata.get("curated_snapshot")):
            continue
        windows = parse_weekly_hours(str(chunk.get("text") or ""))
        if not windows:
            continue
        title_terms = _terms(str(chunk.get("title") or ""))
        overlap = len(question_terms & title_terms)
        if question_terms and not overlap:
            continue
        candidates.append((overlap, chunk, windows))
    if not candidates:
        return None
    candidates.sort(key=lambda item: -item[0])
    return candidates[0][1], candidates[0][2]


def direct_office_hours_answer(
    question: str,
    chunks: list[dict],
    retrieval_status: dict | None = None,
) -> str | None:
    q = (question or "").lower()
    if not re.search(r"\b(?:hours?|open|close[sd]?|closing)\b", q):
        return None
    selected = _source_for_question(question, chunks)
    if selected is None:
        return None
    source, windows = selected
    content = str(source.get("text") or "")
    asks_location = bool(re.search(r"\b(?:where|location|located|address)\b", q))
    address_match = _ADDRESS_RE.search(content)
    if asks_location and address_match is None:
        return None

    request_context = (retrieval_status or {}).get("request_context") or {}
    raw_now = request_context.get("current_datetime")
    try:
        now = datetime.fromisoformat(str(raw_now)) if raw_now else None
    except ValueError:
        now = None
    status = calculate_office_status(windows, now=now)
    title = str(source.get("title") or "Campus office").strip()
    url = str(source.get("source_url") or "").strip()
    day_hours = regular_hours_for_day(windows, status.current_time.weekday())

    lines = [f"**{title}**"]
    if address_match:
        lines.append(f"Location: {address_match.group(0).strip()}")
    phone = _PHONE_RE.search(content)
    email = _EMAIL_RE.search(content)
    if phone:
        lines.append(f"Phone: {phone.group(0)}")
    if email:
        lines.append(f"Email: {email.group(0)}")
    if day_hours:
        lines.append(f"Published {_day_name(status.current_time.weekday())} hours: {day_hours}")

    transition = status.next_transition
    countdown = format_duration(status.minutes_until_transition)
    if status.is_open and transition:
        lines.append(f"**Open now — closes at {format_clock(transition)} (in {countdown}).**")
    elif transition:
        lines.append(
            f"**Closed now — opens {_day_name(transition.weekday())} at {format_clock(transition)} "
            f"(in {countdown}).**"
        )
    else:
        lines.append("**Closed now. No next regular opening could be calculated from the published schedule.**")

    lines.append(
        "This status uses the office's regular published hours in America/Chicago; "
        "a date-specific university closure would override the regular schedule."
    )
    if url:
        lines.append(f"Source: [{title}]({url})")
    return "\n\n".join(lines)


def _day_name(weekday: int) -> str:
    return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[weekday]
