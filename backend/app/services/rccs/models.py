"""Typed models for Registry-Constrained Hybrid Retrieval (RCCS)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DetectedEntity:
    raw_text: str
    normalized_name: str
    entity_type: str  # faculty_or_staff | campus_organization | program | other
    aliases: list[str] = field(default_factory=list)


@dataclass
class RetrievalClassification:
    primary_intent: str
    secondary_intents: list[str]
    entities: list[DetectedEntity]
    freshness: str  # stable | current | unknown
    use_kb: bool
    use_official_live: bool
    use_companions: bool
    companion_categories: list[str]
    registry_topics: list[str]
    routing_reason: str
    confidence: float


@dataclass
class RetrievalPlan:
    use_kb: bool
    use_official_live: bool
    companion_source_ids: list[str]
    official_source_ids: list[str]
    search_queries: list[str]
    entity_queries: list[str]
    freshness: str
    max_results_per_channel: int
    reason: str
    companion_categories: list[str] = field(default_factory=list)
    primary_intent: str = ""
    """Domains the classifier authorized for search/open (apex hosts)."""
    browse_domains: list[str] = field(default_factory=list)
    """When True, page-open agent may fetch full HTML for selected SERP URLs."""
    allow_open_web: bool = False
    browse_social: bool = False
    max_pages_to_open: int = 0


@dataclass
class CompanionSource:
    source_id: str
    name: str
    description: str
    content_type: str
    source_tier: str
    category: str
    base_url: str
    url_template: str
    domain_allowlist: list[str]
    query_template: str
    fetch_mode: str
    trust_level: str
    entity_types: list[str]
    topic_keywords: set[str]
    aliases: list[str]
    enabled: bool
    allowed_for_ai_retrieval: bool
    allow_chroma_ingest: bool
    citation_label: str
    notes: str = ""


@dataclass
class RetrievedEvidence:
    evidence_id: str
    title: str
    url: str | None
    text: str
    source_id: str
    source_name: str
    source_tier: str  # A | B | C
    trust_level: str
    category: str
    retrieval_channel: str  # kb | official_live | companion
    published_at: datetime | None
    fetched_at: datetime
    relevance_score: float
    rerank_score: float | None = None
    entity_match_score: float | None = None
    is_link_only: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_chunk_dict(self) -> dict[str, Any]:
        """Shape expected by llm.generate_answer / existing ChunkResponse mapping."""
        return {
            "text": self.text,
            "title": self.title,
            "source_url": self.url or "",
            "chunk_id": self.evidence_id,
            "category": self.category,
            "score": self.relevance_score,
            "source_tier": self.source_tier,
            "trust_level": self.trust_level,
            "retrieval_channel": self.retrieval_channel,
            "is_link_only": self.is_link_only,
            "source_id": self.source_id,
            "citation_label": self.metadata.get("citation_label", ""),
        }

    def to_citation(self) -> dict[str, Any]:
        """SSE / frontend-compatible citation with additive governance fields."""
        return {
            "id": self.evidence_id,
            "title": self.title,
            "url": self.url or "",
            "snippet": (self.text[:200] if self.text else ""),
            "source_id": self.source_id,
            "source_tier": self.source_tier,
            "trust_level": self.trust_level,
            "category": self.category,
            "retrieval_channel": self.retrieval_channel,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "fetched_at": self.fetched_at.isoformat(),
            "is_link_only": self.is_link_only,
        }


@dataclass
class HybridRetrievalResult:
    evidence: list[RetrievedEvidence]
    classification: RetrievalClassification
    plan: RetrievalPlan
    metadata: dict[str, Any] = field(default_factory=dict)
    errors_by_channel: dict[str, str] = field(default_factory=dict)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
