"""Load and validate campus-intelligence configuration.

The registry contains routing semantics and source ownership only. It must not
contain time-sensitive university facts.
"""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parents[4]
_DATA = _ROOT / "knowledge" / "campus_intelligence"
_VALID_STATUSES = {
    "fully_supported", "live_official", "limited", "authenticated_only", "unavailable"
}
_VALID_FRESHNESS = {"static", "term_based", "live", "personal"}
_VALID_RISK = {"low", "medium", "high"}
_VALID_ROUTE_STATES = {
    "FORBIDDEN", "NOT_APPLICABLE", "FALLBACK", "CONDITIONAL", "PRIMARY", "REQUIRED"
}


class CampusIntelligenceConfigurationError(RuntimeError):
    """Raised when a versioned machine-readable architecture contract is invalid."""


def _load_json(name: str) -> dict[str, Any]:
    path = _DATA / name
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampusIntelligenceConfigurationError(f"invalid {name}: {exc}") from exc
    if not isinstance(data, dict) or not data.get("version"):
        raise CampusIntelligenceConfigurationError(f"{name} requires a version")
    return data


@lru_cache(maxsize=1)
def load_domain_pack_registry() -> dict[str, Any]:
    data = _load_json("domain_packs.json")
    packs: dict[str, dict[str, Any]] = {}
    for raw in data.get("packs") or []:
        domain_id = str(raw.get("domain_id") or "").strip()
        if not domain_id or domain_id in packs:
            raise CampusIntelligenceConfigurationError(f"duplicate/empty domain pack: {domain_id!r}")
        if raw.get("status") not in _VALID_STATUSES:
            raise CampusIntelligenceConfigurationError(f"invalid status for {domain_id}")
        intents = set(raw.get("supported_intents") or [])
        if not intents:
            raise CampusIntelligenceConfigurationError(f"{domain_id} has no supported intents")
        for intent, defaults in (raw.get("intent_defaults") or {}).items():
            if intent not in intents:
                raise CampusIntelligenceConfigurationError(f"{domain_id}.{intent} is not supported")
            if defaults.get("freshness") not in _VALID_FRESHNESS:
                raise CampusIntelligenceConfigurationError(f"invalid freshness for {domain_id}.{intent}")
            if defaults.get("risk") not in _VALID_RISK:
                raise CampusIntelligenceConfigurationError(f"invalid risk for {domain_id}.{intent}")
            if not defaults.get("answer_shape"):
                raise CampusIntelligenceConfigurationError(f"missing answer shape for {domain_id}.{intent}")
        packs[domain_id] = raw
    default_domain = data.get("default_domain")
    if default_domain not in packs:
        raise CampusIntelligenceConfigurationError("default domain pack does not exist")
    return {"version": data["version"], "default_domain": default_domain, "packs": packs}


def get_domain_pack(domain_id: str) -> dict[str, Any] | None:
    pack = load_domain_pack_registry()["packs"].get(domain_id)
    return deepcopy(pack) if pack else None


@lru_cache(maxsize=1)
def load_source_group_registry() -> dict[str, Any]:
    data = _load_json("source_groups.json")
    groups: dict[str, dict[str, Any]] = {}
    for raw in data.get("groups") or []:
        group_id = str(raw.get("source_group_id") or "").strip()
        if not group_id or group_id in groups:
            raise CampusIntelligenceConfigurationError(f"duplicate/empty source group: {group_id!r}")
        required = {
            "owner_domains", "allowed_intents", "trust_tier", "content_types",
            "freshness_sensitivity", "crawl_strategy", "parsing_strategy",
            "authentication", "action_links_expected", "fallback_behavior",
        }
        missing = sorted(required - set(raw))
        if missing:
            raise CampusIntelligenceConfigurationError(f"{group_id} missing {missing}")
        groups[group_id] = raw
    return {"version": data["version"], "groups": groups}


def get_source_group(group_id: str) -> dict[str, Any] | None:
    group = load_source_group_registry()["groups"].get(group_id)
    return deepcopy(group) if group else None


@lru_cache(maxsize=1)
def load_route_policy_registry() -> dict[str, Any]:
    data = _load_json("route_policies.json")
    declared_channels = set(data.get("channels") or [])
    if not declared_channels:
        raise CampusIntelligenceConfigurationError("route policies declare no channels")
    for template_name, template in (data.get("templates") or {}).items():
        channels = template.get("channels") or {}
        if set(channels) != declared_channels:
            raise CampusIntelligenceConfigurationError(
                f"route template {template_name} must decide every channel"
            )
        for channel, decision in channels.items():
            if decision.get("state") not in _VALID_ROUTE_STATES or not decision.get("reason"):
                raise CampusIntelligenceConfigurationError(
                    f"invalid decision for {template_name}.{channel}"
                )
    for policy in data.get("policies") or []:
        if policy.get("template") not in data.get("templates", {}):
            raise CampusIntelligenceConfigurationError(
                f"unknown route template {policy.get('template')}"
            )
    return data


@lru_cache(maxsize=1)
def load_answer_shapes() -> dict[str, Any]:
    return _load_json("answer_shapes.json")


@lru_cache(maxsize=1)
def load_failure_taxonomy() -> dict[str, Any]:
    return _load_json("failure_taxonomy.json")


def capability_snapshot(*, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return self-knowledge derived from configuration and measured coverage."""
    runtime = runtime or {}
    registry = load_domain_pack_registry()
    groups = load_source_group_registry()["groups"]
    try:
        from app.services.index_manifest import get_index_manifest_summary

        coverage = get_index_manifest_summary()
    except Exception:
        coverage = {"available": False, "by_source_group": {}}
    group_coverage = coverage.get("by_source_group") or {}
    live_available = bool(
        runtime.get("official_web_search_available")
        and runtime.get("web_browsing_enabled", True)
    )
    by_status: dict[str, list[dict[str, Any]]] = {
        status: [] for status in _VALID_STATUSES
    }
    downgraded: list[str] = []
    for pack in registry["packs"].values():
        group_ids = [g for g in pack.get("source_groups", []) if g in groups]
        declared_status = pack["status"]
        effective_status = declared_status
        uncovered = [
            group_id for group_id in group_ids
            if int((group_coverage.get(group_id) or {}).get("indexed", 0)) == 0
        ] if coverage.get("available") else []
        if declared_status == "fully_supported" and uncovered:
            effective_status = "live_official" if live_available else "limited"
            downgraded.append(pack["domain_id"])
        elif declared_status == "live_official" and not live_available:
            effective_status = "limited"
            downgraded.append(pack["domain_id"])
        item = {
            "domain_id": pack["domain_id"],
            "subdomains": list(pack.get("subdomains") or []),
            "supported_intents": list(pack.get("supported_intents") or []),
            "source_groups": group_ids,
            "specialist_candidate": any(groups[g].get("structured") for g in group_ids),
            "declared_status": declared_status,
            "effective_status": effective_status,
            "unindexed_source_groups": uncovered,
        }
        by_status[effective_status].append(item)
    for values in by_status.values():
        values.sort(key=lambda item: item["domain_id"])
    limitations = [
        "Personal records require an authenticated McNeese system.",
        "Live and term-based claims require current official verification.",
        "Registered sources are not described as indexed unless the index manifest confirms them.",
    ]
    if downgraded:
        limitations.append(
            "Configured support was downgraded for domains with unindexed required source groups: "
            + ", ".join(sorted(downgraded))
            + "."
        )
    return {
        "registry_version": registry["version"],
        "domains_by_status": by_status,
        "runtime": runtime,
        "coverage_available": bool(coverage.get("available")),
        "downgraded_domains": sorted(downgraded),
        "limitations": limitations,
    }


def source_groups_for(*, source_id: str = "", url: str = "") -> list[str]:
    """Resolve governed ownership for runtime evidence without guessing facts."""
    sid = (source_id or "").strip()
    normalized_url = (url or "").strip().rstrip("/").lower()
    matched: list[str] = []
    for group_id, group in load_source_group_registry()["groups"].items():
        if sid and sid in (group.get("source_ids") or []):
            matched.append(group_id)
            continue
        for prefix in group.get("url_prefixes") or []:
            normalized_prefix = str(prefix or "").strip().rstrip("/").lower()
            if normalized_url and normalized_prefix and normalized_url.startswith(normalized_prefix):
                matched.append(group_id)
                break
    return list(dict.fromkeys(matched))

def clear_configuration_caches() -> None:
    load_domain_pack_registry.cache_clear()
    load_source_group_registry.cache_clear()
    load_route_policy_registry.cache_clear()
    load_answer_shapes.cache_clear()
    load_failure_taxonomy.cache_clear()



