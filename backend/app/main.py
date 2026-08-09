"""AskMcNeese API entrypoint.

Run locally from the `backend/` folder:

    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

If port 8000 is unavailable, use --port 8001 and point the frontend
VITE_API_BASE_URL at the same host/port.

Provides RAG-backed campus Q&A (ChromaDB retrieval, optional live web search when
requested, Claude structured answers). No authentication; public McNeese sources only.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.request_guard import AskRequestGuardMiddleware
from app.routers import ask, class_planner, guest, health
from app.services.class_planner.pipeline import start_sync_scheduler, stop_sync_scheduler

app = FastAPI(
    title="AskMcNeese API",
    version=__version__,
    description=(
        "RAG-backed AskMcNeese assistant: ChromaDB retrieval, structured answers, "
        "optional live mcneese.edu web search when use_web_search=true. No authentication."
    ),
)

# Process-local safety net for the expensive public endpoint. The production
# gateway should enforce the same limits across all workers.
app.add_middleware(AskRequestGuardMiddleware)

_default_origins = "http://127.0.0.1:5173,http://localhost:5173"


def _cors_origins() -> list[str]:
    # Prefer CORS_ALLOWED_ORIGINS; also accept the legacy CORS_ALLOW_ORIGINS alias.
    raw = os.getenv("CORS_ALLOWED_ORIGINS") or os.getenv("CORS_ALLOW_ORIGINS") or _default_origins
    return [item.strip() for item in raw.split(",") if item.strip()]


# Credentials require explicit origins (never "*"). Guest tour uses PATCH + cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Last-Event-ID", "content-type", "accept", "last-event-id"],
    expose_headers=["Content-Type"],
    max_age=600,
)

app.include_router(health.router)
app.include_router(ask.router)
app.include_router(class_planner.router)
app.include_router(guest.router)


@app.on_event("startup")
def start_background_services() -> None:
    start_sync_scheduler()


@app.on_event("shutdown")
def stop_sync_scheduler_event() -> None:
    stop_sync_scheduler()


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "service": "askmcneese-api",
        "version": __version__,
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "ask_stats": "/ask/stats",
            "class_planner_terms": "/class-planner/terms",
            "class_planner_courses": "/class-planner/courses",
            "guest_bootstrap": "/guest/bootstrap",
            "guest_tour": "/guest/tour",
        },
    }
