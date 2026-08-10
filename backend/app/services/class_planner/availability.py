"""Bounded targeted availability refreshes; metadata remains last-known-good."""
from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Iterable

from .models import SectionRecord
from .pipeline import McNeeseClassSearchAdapter, parse_sections, validate_sections
from .store import ClassPlannerStore

LOGGER = logging.getLogger(__name__)


def refresh_course_availability(
    term_id: str, course_id: str, *, store: ClassPlannerStore | None = None,
    adapter: McNeeseClassSearchAdapter | None = None,
) -> dict[str, object]:
    store = store or ClassPlannerStore.from_environment()
    course = store.get_course(term_id, course_id)
    if course is None:
        return {"status": "not_found", "updated": 0}
    token = store.acquire_sync_lock(term_id, scope=f"availability:{course_id}")
    if not token:
        return {"status": "in_progress", "updated": 0}
    owns_adapter = adapter is None
    adapter = adapter or McNeeseClassSearchAdapter(timeout_seconds=35, max_attempts=2)
    try:
        html = adapter.fetch_sections_html(
            term_id, subject=str(course["subject"]), course_number=str(course["courseNumber"]),
        )
        parsed = parse_sections(html, term_id, allow_empty=True)
        valid = [item for item in validate_sections(parsed).valid if item.course_id == course_id]
        if not valid:
            return {"status": "unavailable", "updated": 0}
        verified_at = datetime.now(UTC).isoformat()
        updated = store.update_availability(valid, verified_at)
        return {"status": "verified", "updated": updated, "verifiedAt": verified_at}
    except Exception as exc:
        LOGGER.warning("targeted availability refresh failed for %s: %s", course_id, exc)
        return {"status": "unavailable", "updated": 0, "error": str(exc)}
    finally:
        store.release_sync_lock(term_id, token, scope=f"availability:{course_id}")
        if owns_adapter:
            adapter.close()


def refresh_active_courses(term_id: str, course_ids: Iterable[str]) -> dict[str, object]:
    store = ClassPlannerStore.from_environment()
    results = [refresh_course_availability(term_id, course_id, store=store) for course_id in course_ids]
    return {
        "status": "complete",
        "courses": len(results),
        "updated": sum(int(item.get("updated", 0)) for item in results),
        "unavailable": sum(item.get("status") == "unavailable" for item in results),
    }
