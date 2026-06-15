"""PM-03 — health check router.

`GET /health` is the lightweight endpoint the frontend pings on load to confirm
the backend is up. It must stay cheap (no DB calls, no network).
"""

from fastapi import APIRouter

from app import __version__

router = APIRouter(tags=["health"])

SERVICE_NAME = "askmcneese-api"


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE_NAME, "version": __version__}
