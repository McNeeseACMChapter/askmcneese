"""Normalized Class Planner API with bounded pagination and protected sync triggers."""
from __future__ import annotations

from functools import lru_cache
import hmac
import os

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query

from app.services.class_planner.availability import refresh_active_courses, refresh_course_availability
from app.services.class_planner.pipeline import sync_mcneese_term
from app.services.class_planner.store import ClassPlannerStore

router = APIRouter(prefix="/class-planner", tags=["class-planner"])


@lru_cache(maxsize=1)
def _store() -> ClassPlannerStore:
    return ClassPlannerStore.from_environment()


def _source_or_503(term_id: str) -> dict[str, object]:
    source = _store().freshness(term_id)
    if source is None:
        raise HTTPException(status_code=503, detail="No validated McNeese class dataset has been published for this term.")
    return source


def _authorize(token: str | None) -> None:
    expected = os.getenv("CLASS_SYNC_ADMIN_TOKEN", "")
    if not expected or not token or not hmac.compare_digest(expected, token):
        raise HTTPException(status_code=401, detail="Invalid Class Planner sync token.")


@router.get("/terms")
def list_terms() -> dict[str, object]:
    data = _store().list_terms()
    if not data:
        raise HTTPException(status_code=503, detail="No validated McNeese class dataset is available.")
    return {"data": data, "source": {"name": "McNeese Class Search"}}


@router.get("/courses")
def search_courses(
    term: str = Query(..., min_length=1), q: str = "", open: bool = False,
    online: bool = False, days: str = "",
    time: str = Query("any", pattern="^(any|morning|afternoon|evening)$"),
    limit: int = Query(40, ge=1, le=100),
) -> dict[str, object]:
    source = _source_or_503(term)
    normalized_days = tuple(day for day in days.upper().split(",") if day)
    data = _store().search_courses(term, query=q, open_only=open, online_only=online,
        days=normalized_days, time_of_day=time, limit=limit)
    return {"data": data, "source": source, "pagination": {"limit": limit, "count": len(data)}}


@router.get("/courses/{course_id}/sections")
def course_sections(
    course_id: str, background_tasks: BackgroundTasks, term: str = Query(..., min_length=1),
    limit: int = Query(6, ge=1, le=24), offset: int = Query(0, ge=0), selected: str = "",
) -> dict[str, object]:
    source = _source_or_503(term)
    if _store().get_course(term, course_id) is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    data = _store().get_course_sections(term, course_id, limit=limit, offset=offset,
        selected_ids=tuple(item for item in selected.split(",") if item))
    if source.get("availabilityState") == "stale":
        background_tasks.add_task(refresh_course_availability, term, course_id, store=_store())
    return {"data": data, "source": source}


@router.get("/courses/{course_id}")
def course(course_id: str, term: str = Query(..., min_length=1)) -> dict[str, object]:
    source = _source_or_503(term)
    data = _store().get_course(term, course_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return {"data": data, "source": source}


@router.get("/sections/{section_id:path}")
def section(section_id: str, verify: bool = False) -> dict[str, object]:
    data = _store().get_section(section_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Section not found.")
    verification = None
    if verify:
        verification = refresh_course_availability(str(data["termId"]), str(data["courseId"]), store=_store())
        refreshed = _store().get_section(section_id)
        if refreshed is not None:
            data = refreshed
    return {"data": data, "source": _source_or_503(str(data["termId"])), "verification": verification}


@router.get("/freshness")
def freshness(term: str = Query(..., min_length=1)) -> dict[str, object]:
    return {"data": _source_or_503(term)}


@router.post("/internal/sync", status_code=202)
def trigger_sync(background_tasks: BackgroundTasks, term: str = Query(..., min_length=1),
    x_class_sync_token: str | None = Header(None)) -> dict[str, object]:
    _authorize(x_class_sync_token)
    background_tasks.add_task(sync_mcneese_term, term)
    return {"status": "accepted", "term": term, "kind": "full"}


@router.post("/internal/availability", status_code=202)
def trigger_availability(background_tasks: BackgroundTasks, term: str = Query(..., min_length=1),
    courses: str = "", x_class_sync_token: str | None = Header(None)) -> dict[str, object]:
    _authorize(x_class_sync_token)
    course_ids = [item for item in courses.split(",") if item] or _store().active_courses(term)
    background_tasks.add_task(refresh_active_courses, term, course_ids)
    return {"status": "accepted", "term": term, "kind": "availability", "courses": len(course_ids)}
