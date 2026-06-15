"""AskMcNeese API entrypoint (Sprint 1).

Run locally from the `backend/` folder:

    uvicorn app.main:app --reload

Sprint 1 scope is intentionally tiny: a health check the frontend can call. No
LLM, no auth, no student data.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.routers import health

app = FastAPI(
    title="AskMcNeese API",
    version=__version__,
    description="Backend API for the AskMcNeese assistant (Sprint 1 foundation).",
)

# Frontend (React/Vite dev server) needs to call /health from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the real frontend origin before production
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {"service": "askmcneese-api", "health": "/health", "docs": "/docs"}
