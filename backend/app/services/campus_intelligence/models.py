"""Typed contracts shared by all campus-intelligence domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CampusQuery:
    original_query: str
    normalized_query: str
    domain: str
    subdomain: str | None
    intent: str
    action: str | None
    entities: dict[str, str | int | float | bool | None]
    audience: str
    freshness: str
    risk: str
    answer_shape: str
    required_source_groups: list[str]
    required_fields: list[str]
    confidence: float
    ambiguities: list[str] = field(default_factory=list)
    clarification_required: bool = False
    compiler_version: str = "1.1.0"
    decision_reasons: list[str] = field(default_factory=list)
    # Full-spectrum research-pack fields (optional; empty when pack unavailable).
    category_id: str | None = None
    category: str | None = None
    parent_domain: str | None = None
    subcategory_id: str | None = None
    subcategory: str | None = None
    research_intent: str | None = None
    preferred_domains: list[str] = field(default_factory=list)
    answer_schema: str | None = None
    freshness_class: str | None = None
    seed_entity: str | None = None
    planned_queries: list[dict[str, Any]] = field(default_factory=list)
    source_policy_ids: list[str] = field(default_factory=list)
    requires_live_discovery: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChannelDecision:
    channel: str
    state: str
    reason: str
    condition: str | None = None
    timeout_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolvedRoutePolicy:
    domain: str
    intent: str
    template: str
    precedence: list[str]
    concurrency_groups: list[list[str]]
    channels: dict[str, ChannelDecision]
    policy_version: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["channels"] = {
            key: value.to_dict() for key, value in self.channels.items()
        }
        return data


@dataclass
class RouteAttempt:
    route: str
    source_group: str | None
    status: str
    reason: str
    latency_ms: int = 0
    result_count: int = 0
    failure_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryRouteTrace:
    query_id: str | None
    compiled_query: dict[str, Any]
    route_policy: dict[str, Any]
    attempts: list[RouteAttempt] = field(default_factory=list)
    rejected_evidence: list[dict[str, Any]] = field(default_factory=list)
    field_coverage: dict[str, bool] = field(default_factory=dict)
    sufficiency: dict[str, Any] = field(default_factory=dict)
    renderer: str | None = None
    timings_ms: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "compiled_query": self.compiled_query,
            "route_policy": self.route_policy,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "rejected_evidence": self.rejected_evidence,
            "field_coverage": self.field_coverage,
            "sufficiency": self.sufficiency,
            "renderer": self.renderer,
            "timings_ms": self.timings_ms,
        }


@dataclass(frozen=True)
class EvidenceSufficiencyResult:
    passed: bool
    score: float
    required_fields: list[str]
    field_coverage: dict[str, bool]
    missing_fields: list[str]
    covered_source_groups: list[str]
    missing_source_groups: list[str]
    accepted_evidence_ids: list[str]
    rejected_evidence: list[dict[str, str]]
    failure_codes: list[str]
    next_permitted_route: str | None
    partial_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SpecialistResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    source_attempts: list[dict[str, Any]] = field(default_factory=list)
    field_coverage: dict[str, bool] = field(default_factory=dict)
    freshness: dict[str, Any] = field(default_factory=dict)
    failures: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "evidence": [
                item.to_citation() if hasattr(item, "to_citation") else item
                for item in self.evidence
            ],
            "source_attempts": self.source_attempts,
            "field_coverage": self.field_coverage,
            "freshness": self.freshness,
            "failures": self.failures,
            "latency_ms": self.latency_ms,
        }
