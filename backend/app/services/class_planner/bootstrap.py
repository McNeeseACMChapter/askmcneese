"""Non-blocking first-deploy bootstrap for the live Class Planner dataset."""
from __future__ import annotations

import logging
import os
from threading import Lock, Thread

from app.services.class_planner.pipeline import sync_mcneese_term
from app.services.class_planner.store import ClassPlannerStore

LOGGER = logging.getLogger(__name__)
_START_LOCK = Lock()
_STARTED = False


def _enabled() -> bool:
    configured = os.getenv("CLASS_BOOTSTRAP_ON_START")
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    # Existing Render services might predate the Blueprint variables. Fail toward
    # real source data there, while keeping local/test startup network-free.
    return os.getenv("RENDER", "false").strip().lower() == "true"


def configured_terms() -> tuple[str, ...]:
    raw = os.getenv("CLASS_BOOTSTRAP_TERM_IDS") or os.getenv("CLASS_SYNC_TERM_ID", "")
    if not raw and os.getenv("RENDER", "false").strip().lower() == "true":
        raw = "202660"
    return tuple(dict.fromkeys(item.strip() for item in raw.split(",") if item.strip()))


def bootstrap_missing_terms(*, store: ClassPlannerStore | None = None) -> None:
    """Publish configured terms only when their validated dataset is absent."""
    target = store or ClassPlannerStore.from_environment()
    for term_id in configured_terms():
        if target.freshness(term_id) is not None:
            LOGGER.info("class planner bootstrap skipped; term %s is already published", term_id)
            continue
        try:
            LOGGER.info("class planner bootstrap started for term %s", term_id)
            sync_mcneese_term(term_id, store=target)
        except Exception:
            # The API remains available and reports 503 for unpublished data. Scheduled
            # sync can retry without turning a source outage into an application outage.
            LOGGER.exception("class planner bootstrap failed for term %s", term_id)


def start_class_planner_bootstrap() -> bool:
    """Start at most one background bootstrap per web process."""
    global _STARTED
    if not _enabled() or not configured_terms():
        return False
    with _START_LOCK:
        if _STARTED:
            return False
        _STARTED = True
    Thread(target=bootstrap_missing_terms, name="class-planner-bootstrap", daemon=True).start()
    return True
