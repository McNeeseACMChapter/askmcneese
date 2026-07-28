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
from app.routers import health, ask

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
_cors_origins = [
    item.strip()
    for item in os.getenv("CORS_ALLOWED_ORIGINS", _default_origins).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["content-type", "accept", "last-event-id"],
)

app.include_router(health.router)
app.include_router(ask.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "service": "askmcneese-api",
        "version": __version__,
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "ask_stats": "/ask/stats",
        },
    }
