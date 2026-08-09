"""Read-only normalized Class Planner API."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from app.services.class_planner.store import ClassPlannerStore

router = APIRouter(prefix="/class-planner", tags=["class-planner"])


@lru_cache(maxsize=1)
def _store() -> ClassPlannerStore:
    return ClassPlannerStore.from_environment()


def _source_or_503(term_id: str) -> dict[str, object]:
    source = _store().freshness(term_id)
    if source is None:
        raise HTTPException(
            status_code=503,
            detail="No validated McNeese class dataset has been published for this term.",
        )
    return source


@router.get("/terms")
def terms() -> dict[str, object]:
    data = _store().list_terms()
    if not data:
        raise HTTPException(
            status_code=503,
            detail="No validated McNeese class dataset is available.",
        )
    return {"data": data, "source": {"name": "McNeese Class Search"}}


@router.get("/courses")
def courses(
    term: str = Query(..., min_length=1),
    q: str = "",
    open: bool = False,
    online: bool = False,
    days: str = "",
    time: str = Query("any", pattern="^(any|morning|afternoon|evening)$"),
) -> dict[str, object]:
    source = _source_or_503(term)
    normalized_days = tuple(day for day in days.upper().split(",") if day)
    data = _store().search_courses(
        term,
        query=q,
        open_only=open,
        online_only=online,
        days=normalized_days,
        time_of_day=time,
    )
    return {"data": data, "source": source}


@router.get("/courses/{course_id:path}")
def course(course_id: str, term: str = Query(..., min_length=1)) -> dict[str, object]:
    source = _source_or_503(term)
    data = _store().get_course(term, course_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return {"data": data, "source": source}


@router.get("/sections/{section_id:path}")
def section(section_id: str) -> dict[str, object]:
    data = _store().get_section(section_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Section not found.")
    source = _source_or_503(str(data["termId"]))
    return {"data": data, "source": source}


@router.get("/freshness")
def freshness(term: str = Query(..., min_length=1)) -> dict[str, object]:
    return {"data": _source_or_503(term)}

