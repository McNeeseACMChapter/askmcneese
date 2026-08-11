"""Deterministic answers from a freshly read McNeese academic schedule.

The parser contains no academic dates. It extracts rows from the evidence page
selected by live retrieval, which avoids an unnecessary LLM call for simple
calendar questions while preserving source freshness and provenance.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CalendarEvent:
    event: str
    event_date: date
    section: str = "regular"

    @property
    def display_date(self) -> str:
        return f"{self.event_date:%A, %B} {self.event_date.day}, {self.event_date.year}"


def _extract_events(content: str, *, default_year: int | None = None) -> list[CalendarEvent]:
    current_month: int | None = None
    current_year: int | None = default_year
    current_section = "regular"
    events: list[CalendarEvent] = []
    month_lookup = {
        name.upper(): number
        for number, name in enumerate(calendar.month_name)
        if name
    }
    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        cells = [cell.strip() for cell in line.strip("|").split("|")]

        if len(cells) >= 2 and cells[0] and all(not cell for cell in cells[1:]):
            heading = re.sub(r"\s+", " ", cells[0]).strip().lower()
            if "session" in heading:
                current_section = "regular" if "regular" in heading else heading
                continue

        month_match = re.match(r"^\|\s*([A-Z]+)\s+(20\d{2})\s*\|", line)
        if month_match and month_match.group(1) in month_lookup:
            current_month = month_lookup[month_match.group(1)]
            current_year = int(month_match.group(2))
            continue

        if current_month is not None and current_year is not None:
            row = re.match(
                r"^\|\s*(\d{1,2})\s*\|\s*[^|]+?\s*\|\s*([^|]+?)\s*\|",
                line,
            )
            if row:
                try:
                    event_date = date(current_year, current_month, int(row.group(1)))
                except ValueError:
                    event_date = None
                event = re.sub(r"\s+", " ", row.group(2)).strip()
                if event_date and event and event != "---":
                    events.append(
                        CalendarEvent(
                            event=event,
                            event_date=event_date,
                            section=current_section,
                        )
                    )
                    continue

        # The regular Summer calendar is published as ``Event | Month Day``
        # instead of the three-column Fall/Spring month tables.
        if len(cells) != 2 or current_year is None:
            continue
        event = re.sub(r"\s+", " ", cells[0]).strip()
        date_match = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2})", cells[1])
        if not event or not date_match:
            continue
        month_number = month_lookup.get(date_match.group(1).upper())
        if month_number is None:
            continue
        try:
            event_date = date(current_year, month_number, int(date_match.group(2)))
        except ValueError:
            continue
        events.append(
            CalendarEvent(
                event=event,
                event_date=event_date,
                section=current_section,
            )
        )
    return events


def _select_event(question: str, events: list[CalendarEvent]) -> CalendarEvent | None:
    if not events:
        return None
    q = (question or "").lower()
    asks_start = bool(re.search(r"\b(start|starts|starting|begin|begins|opening)\b", q))
    asks_end = bool(re.search(r"\b(end|ends|ending|finish|finishes|over)\b", q))
    asks_final = "final" in q or "exam" in q
    requested_session = re.search(r"\bsession\s+([a-z0-9]+)\b", q)

    def score(item: CalendarEvent) -> tuple[int, int]:
        event = item.event.lower()
        section = item.section.lower()
        event_and_section = f"{event} {section}"
        value = 0
        event_session = re.search(r"\bsession\s+([a-z0-9]+)\b", event_and_section)
        if requested_session:
            value += 30 if requested_session.group(1) in event_and_section else -30
        elif event_session:
            # Generic semester questions refer to the regular term, not a
            # short session whose similarly named rows appear later.
            value -= 30
        elif section == "regular":
            value += 10
        if asks_final:
            value += 12 if "final" in event and "exam" in event else -8
        elif "final" in event:
            value -= 5
        if asks_start:
            value += 28 if event == "classes begin" else 0
            value += 20 if "classes begin" in event else 0
            value += 8 if "begin" in event or "start" in event else 0
            value -= 8 if "end" in event else 0
        if asks_end:
            if "semester" in q:
                value += 35 if "semester ends" in event else 0
            if "class" in q:
                value += 28 if event == "classes end" else 0
                value += 20 if "classes end" in event else 0
            value += 8 if "end" in event else 0
            value -= 8 if "begin" in event or "start" in event else 0
        query_terms = {
            term
            for term in re.findall(r"[a-z0-9]+", q)
            if len(term) > 3 and term not in {"when", "what", "mcneese", "semester"}
        }
        value += 2 * len(query_terms & set(re.findall(r"[a-z0-9]+", event)))
        return value, -item.event_date.toordinal()

    selected = max(events, key=score)
    return selected if score(selected)[0] > 0 else None


def direct_academic_calendar_answer(question: str, chunks: list[dict]) -> str | None:
    source = next(
        (
            chunk
            for chunk in chunks
            if chunk.get("category") == "academic_calendar"
            and bool((chunk.get("metadata") or {}).get("page_fetched"))
        ),
        None,
    )
    if source is None:
        return None
    title = str(source.get("title") or "the academic schedule").strip()
    url = str(source.get("source_url") or "").strip()
    year_match = re.search(r"\b(20\d{2})\b", f"{title} {url}")
    events = _extract_events(
        str(source.get("text") or ""),
        default_year=int(year_match.group(1)) if year_match else None,
    )

    q = (question or "").lower()
    asks_term_end = bool(re.search(r"\b(end|ends|ending|finish|finishes|over)\b", q)) and bool(
        re.search(r"\b(semester|session|term)\b", q)
    )
    has_explicit_semester_end = any("semester ends" in item.event.lower() for item in events)
    if asks_term_end and not has_explicit_semester_end:
        regular_classes_end = next(
            (
                item
                for item in events
                if item.section == "regular" and item.event.lower() == "classes end"
            ),
            None,
        )
        regular_finals_end = next(
            (
                item
                for item in events
                if item.section == "regular"
                and item.event.lower().startswith("final examinations end")
            ),
            None,
        )
        if regular_classes_end and regular_finals_end:
            answer = (
                f"**Regular-session classes end on {regular_classes_end.display_date}. "
                f"Final examinations end on {regular_finals_end.display_date}.**"
            )
            if url:
                answer += f"\n\nMcNeese lists these dates on the [{title}]({url}) schedule."
            return answer

    selected = _select_event(question, events)
    if selected is None:
        return None
    event = selected.event.rstrip(".")
    answer = f"**{event} on {selected.display_date}.**"
    if url:
        answer += f"\n\nMcNeese lists this date on the [{title}]({url}) schedule."
    return answer
