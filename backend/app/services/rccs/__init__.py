"""Registry-Constrained Hybrid Retrieval and Companion Search (RCCS)."""

from app.services.rccs.classify import classify_retrieval
from app.services.rccs.config import flags_snapshot
from app.services.rccs.hybrid import hybrid_retrieve
from app.services.rccs.plan import build_retrieval_plan

__all__ = [
    "classify_retrieval",
    "build_retrieval_plan",
    "hybrid_retrieve",
    "flags_snapshot",
]
