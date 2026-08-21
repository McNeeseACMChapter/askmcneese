"""Deterministic campus office-hours parsing and open/closed calculation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


CAMPUS_TIMEZONE = ZoneInfo("America/Chicago")
_DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_DAY_INDEX = {name.lower(): index for index, name in enumerate(_DAY_NAMES)}
_TIME_TEXT = r"\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)"
_HOURS_RE = re.compile(
    rf"\b(?P<first>{'|'.join(_DAY_NAMES)})\b"
    rf"(?:\s*(?:-|–|—|through|thru|to)\s*\b(?P<last>{'|'.join(_DAY_NAMES)})\b)?"
    rf"\s*[:,-]?\s*(?P<opens>{_TIME_TEXT})\s*(?:-|–|—|to)\s*(?P<closes>{_TIME_TEXT})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OfficeWindow:
    weekday: int
    opens: time
    closes: time


@dataclass(frozen=True)
class OfficeStatus:
    is_open: bool
    current_time: datetime
    next_transition: datetime | None
    transition_kind: str | None

    @property
    def minutes_until_transition(self) -> int | None:
        if self.next_transition is None:
            return None
        seconds = max(0, (self.next_transition - self.current_time).total_seconds())
        return max(0, int((seconds + 59) // 60))


def _parse_time(value: str) -> time:
    compact = re.sub(r"\s+", " ", value.strip().lower()).replace(".", "")
    match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)", compact)
    if match is None:
        raise ValueError(f"Unsupported office time: {value}")
    hour = int(match.group(1)) % 12
    if match.group(3) == "pm":
        hour += 12
    return time(hour=hour, minute=int(match.group(2) or 0))


def parse_weekly_hours(content: str) -> list[OfficeWindow]:
    """Extract regular weekly windows without inventing closure exceptions."""
    normalized = re.sub(r"\s+", " ", content or " ")
    windows: list[OfficeWindow] = []
    seen: set[tuple[int, time, time]] = set()
    for match in _HOURS_RE.finditer(normalized):
        first = _DAY_INDEX[match.group("first").lower()]
        last = _DAY_INDEX[(match.group("last") or match.group("first")).lower()]
        if last < first:
            continue
        opens = _parse_time(match.group("opens"))
        closes = _parse_time(match.group("closes"))
        if closes <= opens:
            continue
        for weekday in range(first, last + 1):
            key = (weekday, opens, closes)
            if key not in seen:
                seen.add(key)
                windows.append(OfficeWindow(weekday=weekday, opens=opens, closes=closes))
    return sorted(windows, key=lambda item: (item.weekday, item.opens, item.closes))


def calculate_office_status(
    windows: list[OfficeWindow],
    *,
    now: datetime | None = None,
) -> OfficeStatus:
    current = now.astimezone(CAMPUS_TIMEZONE) if now else datetime.now(CAMPUS_TIMEZONE)
    for window in windows:
        if window.weekday != current.weekday():
            continue
        opens_at = datetime.combine(current.date(), window.opens, tzinfo=CAMPUS_TIMEZONE)
        closes_at = datetime.combine(current.date(), window.closes, tzinfo=CAMPUS_TIMEZONE)
        if opens_at <= current < closes_at:
            return OfficeStatus(True, current, closes_at, "closes")

    candidates: list[datetime] = []
    for offset in range(0, 8):
        day = current.date() + timedelta(days=offset)
        weekday = day.weekday()
        for window in windows:
            if window.weekday != weekday:
                continue
            opens_at = datetime.combine(day, window.opens, tzinfo=CAMPUS_TIMEZONE)
            if opens_at > current:
                candidates.append(opens_at)
    next_open = min(candidates) if candidates else None
    return OfficeStatus(False, current, next_open, "opens" if next_open else None)


def format_duration(minutes: int | None) -> str:
    if minutes is None:
        return ""
    days, remainder = divmod(minutes, 24 * 60)
    hours, mins = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if mins or not parts:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    return " ".join(parts)


def format_clock(value: datetime | time) -> str:
    raw = value.strftime("%I:%M %p").lstrip("0")
    return raw.replace(" AM", " a.m.").replace(" PM", " p.m.")


def regular_hours_for_day(windows: list[OfficeWindow], weekday: int) -> str | None:
    matches = [window for window in windows if window.weekday == weekday]
    if not matches:
        return None
    return ", ".join(f"{format_clock(item.opens)}–{format_clock(item.closes)}" for item in matches)
