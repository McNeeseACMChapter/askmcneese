"""Domain-general campus query compilation and executable routing policy."""

from .compiler import compile_campus_query
from .full_spectrum import (
    build_full_spectrum_plan,
    match_taxonomy,
    pack_available,
    plan_corpus_queries,
)
from .registry import capability_snapshot, get_domain_pack, get_source_group
from .route_policy import resolve_route_policy
from .route_validator import extract_goal_signals, route_matches_goal

__all__ = [
    "compile_campus_query",
    "capability_snapshot",
    "get_domain_pack",
    "get_source_group",
    "resolve_route_policy",
    "pack_available",
    "match_taxonomy",
    "plan_corpus_queries",
    "build_full_spectrum_plan",
    "extract_goal_signals",
    "route_matches_goal",
]
