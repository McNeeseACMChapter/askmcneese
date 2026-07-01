"""AskMcNeese API entrypoint (Sprint 2).

Run locally from the `backend/` folder:

    uvicorn app.main:app --reload

Sprint 2 adds retrieval via POST /ask. Still no LLM, no auth, no student data.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.routers import health, ask

app = FastAPI(
    title="AskMcNeese API",
    version=__version__,
    description="Backend API for the AskMcNeese assistant (Sprint 2 retrieval).",
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
            "docs": "/docs",
        },
    }
