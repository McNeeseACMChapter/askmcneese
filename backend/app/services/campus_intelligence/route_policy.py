"""Resolve executable channel policy for any compiled campus query."""

from __future__ import annotations

from copy import deepcopy

from .models import CampusQuery, ChannelDecision, ResolvedRoutePolicy
from .registry import CampusIntelligenceConfigurationError, load_route_policy_registry


def _matching_policy(domain: str, intent: str, policies: list[dict]) -> dict | None:
    exact = next((p for p in policies if p.get("domain") == domain and p.get("intent") == intent), None)
    if exact:
        return exact
    return next((p for p in policies if p.get("domain") == domain and p.get("intent") == "*"), None)


def resolve_route_policy(query: CampusQuery) -> ResolvedRoutePolicy:
    registry = load_route_policy_registry()
    if query.freshness == "personal":
        template_name = "personal"
    else:
        match = _matching_policy(query.domain, query.intent, registry.get("policies") or [])
        template_name = (match or {}).get("template")
    if not template_name:
        template_name = {
            "static": "static_fact",
            "term_based": "term_fact",
            "live": "live_fact",
            "personal": "personal",
        }.get(query.freshness, "static_fact")
    template = deepcopy((registry.get("templates") or {}).get(template_name))
    if not template:
        raise CampusIntelligenceConfigurationError(f"missing route template {template_name}")
    channels = {
        name: ChannelDecision(
            channel=name,
            state=decision["state"],
            reason=decision["reason"],
            condition=decision.get("condition"),
            timeout_ms=decision.get("timeout_ms"),
        )
        for name, decision in template["channels"].items()
    }
    return ResolvedRoutePolicy(
        domain=query.domain,
        intent=query.intent,
        template=template_name,
        precedence=list(template.get("precedence") or []),
        concurrency_groups=[list(group) for group in (template.get("concurrency_groups") or [])],
        channels=channels,
        policy_version=registry["version"],
    )
