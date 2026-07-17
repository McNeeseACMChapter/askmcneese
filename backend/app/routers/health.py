"""PM-03 — health check router.

`GET /health` is the lightweight endpoint the frontend pings on load to confirm
the backend is up. It stays cheap: no DB calls, no network search — only
non-secret capability booleans.
"""

from fastapi import APIRouter

from app import __version__
from app.services.capabilities import retrieval_capabilities

router = APIRouter(tags=["health"])

SERVICE_NAME = "askmcneese-api"


@router.get("/health")
def health() -> dict:
    caps = retrieval_capabilities()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": __version__,
        "capabilities": caps,
        # Flat aliases for simple frontend consumers
        "knowledge_search_available": caps["knowledge_search_available"],
        "official_web_search_available": caps["official_web_search_available"],
        "hybrid_retrieval_available": caps["hybrid_retrieval_available"],
        "companion_search_available": caps["companion_search_available"],
        "rmp_available": caps["rmp_available"],
        "social_links_available": caps["social_links_available"],
    }
