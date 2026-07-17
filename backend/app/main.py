"""AskMcNeese API entrypoint.

Run locally from the `backend/` folder:

    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

If port 8000 is unavailable, use --port 8001 and point the frontend
VITE_API_BASE_URL at the same host/port.

Provides RAG-backed campus Q&A (ChromaDB retrieval, optional live web search when
requested, Claude structured answers). No authentication; public McNeese sources only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.routers import health, ask

app = FastAPI(
    title="AskMcNeese API",
    version=__version__,
    description=(
        "RAG-backed AskMcNeese assistant: ChromaDB retrieval, structured answers, "
        "optional live mcneese.edu web search when use_web_search=true. No authentication."
    ),
)

# Frontend (React/Vite dev server) needs to call /health and /ask
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the real frontend origin before production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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
