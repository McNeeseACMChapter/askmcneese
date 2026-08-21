"""Full-spectrum McNeese taxonomy, source policy, and query-corpus planning.

Loads the researched pack under knowledge/full_spectrum so retrieval is governed
by the university A-Z information architecture, not employment alone.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parents[4]
_PACK_DIRS = (
    _ROOT / "knowledge" / "full_spectrum",
    _ROOT / "8.3.26 workable" / "mcneese_full_spectrum_search_research_pack",
)
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
_GENERIC = {
    "mcneese", "university", "state", "school", "campus", "the", "and", "for",
    "from", "with", "what", "where", "when", "which", "who", "how", "can",
    "about", "please", "need", "want", "help", "official", "current",
}


@dataclass(frozen=True)
class TaxonomyCategory:
    category_id: str
    category: str
    parent_domain: str
    category_type: str
    aliases: tuple[str, ...]
    official_source_url: str
    risk_tier: str
    subcategories: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class TaxonomyMatch:
    category_id: str
    category: str
    parent_domain: str
    subcategory_id: str | None
    subcategory: str | None
    canonical_pack: str
    aliases_hit: str
    score: float
    official_source_url: str
    risk_tier: str


@dataclass(frozen=True)
class PlannedQuery:
    query_id: str
    query: str
    intent: str
    source_mode: str
    preferred_domains: tuple[str, ...]
    answer_schema: str
    freshness_class: str
    priority_score: int
    risk_level: str
    seed_entity: str


@dataclass(frozen=True)
class FullSpectrumPlan:
    category_id: str | None = None
    category: str | None = None
    parent_domain: str | None = None
    subcategory_id: str | None = None
    subcategory: str | None = None
    canonical_pack: str | None = None
    match_score: float = 0.0
    aliases_hit: str | None = None
    research_intent: str | None = None
    preferred_domains: tuple[str, ...] = ()
    answer_schema: str | None = None
    freshness_class: str | None = None
    risk_level: str | None = None
    seed_entity: str | None = None
    official_source_url: str | None = None
    planned_queries: tuple[PlannedQuery, ...] = ()
    source_policy_ids: tuple[str, ...] = ()
    decision_reasons: tuple[str, ...] = ()


def _pack_dir() -> Path | None:
    for path in _PACK_DIRS:
        if (path / "taxonomy.csv").is_file():
            return path
    return None


def pack_available() -> bool:
    return _pack_dir() is not None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


@lru_cache(maxsize=1)
def load_pack_bridge() -> dict[str, Any]:
    for base in _PACK_DIRS:
        path = base / "pack_bridge.json"
        if path.is_file():
            return json.loads(_read_text(path))
    # Fallback if only the research archive is present without the bridge file.
    knowledge_bridge = _ROOT / "knowledge" / "full_spectrum" / "pack_bridge.json"
    if knowledge_bridge.is_file():
        return json.loads(_read_text(knowledge_bridge))
    return {"version": "0", "parent_domain_to_pack": {}, "category_overrides": {}}


def _tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in _TOKEN_RE.findall((text or "").lower()):
        if token.endswith("'s"):
            token = token[:-2]
        if token in _GENERIC or len(token) <= 1:
            continue
        tokens.add(token)
    return tokens


@lru_cache(maxsize=1)
def load_taxonomy_categories() -> dict[str, TaxonomyCategory]:
    base = _pack_dir()
    if base is None:
        return {}
    path = base / "taxonomy.csv"
    grouped: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            category_id = (row.get("category_id") or "").strip()
            if not category_id:
                continue
            bucket = grouped.setdefault(
                category_id,
                {
                    "category": (row.get("category") or "").strip(),
                    "parent_domain": (row.get("parent_domain") or "").strip(),
                    "category_type": (row.get("category_type") or "").strip(),
                    "aliases": tuple(
                        part.strip()
                        for part in (row.get("aliases") or "").split("|")
                        if part.strip()
                    ),
                    "official_source_url": (row.get("official_source_url") or "").strip(),
                    "risk_tier": (row.get("risk_tier") or "low").strip().lower(),
                    "subcategories": [],
                },
            )
            sub_id = (row.get("subcategory_id") or "").strip()
            sub = (row.get("subcategory") or "").strip()
            if sub_id and sub:
                bucket["subcategories"].append((sub_id, sub))
    out: dict[str, TaxonomyCategory] = {}
    for category_id, raw in grouped.items():
        out[category_id] = TaxonomyCategory(
            category_id=category_id,
            category=raw["category"],
            parent_domain=raw["parent_domain"],
            category_type=raw["category_type"],
            aliases=tuple(raw["aliases"]),
            official_source_url=raw["official_source_url"],
            risk_tier=raw["risk_tier"],
            subcategories=tuple(dict.fromkeys(raw["subcategories"])),
        )
    return out


@lru_cache(maxsize=1)
def load_research_source_registry() -> list[dict[str, str]]:
    base = _pack_dir()
    if base is None:
        return []
    path = base / "source_registry.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def corpus_available() -> bool:
    """True when the large research query dump (or a seed substitute) is present."""
    base = _pack_dir()
    if base is None:
        return False
    return any(
        (base / name).is_file()
        for name in ("search_queries_50000.csv", "search_queries_seed.csv")
    )


@lru_cache(maxsize=1)
def _query_index() -> dict[tuple[str, str], list[dict[str, str]]]:
    """Index corpus rows by (category_id, research_intent)."""
    base = _pack_dir()
    if base is None:
        return {}
    path = next(
        (
            candidate
            for name in ("search_queries_50000.csv", "search_queries_seed.csv")
            if (candidate := base / name).is_file()
        ),
        None,
    )
    if path is None:
        return {}
    index: dict[tuple[str, str], list[dict[str, str]]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            category_id = (row.get("category_id") or "").strip()
            intent = (row.get("intent") or "").strip()
            if not category_id or not intent:
                continue
            bucket = index.setdefault((category_id, intent), [])
            # Keep a bounded high-priority sample per bucket for planning.
            if len(bucket) >= 24:
                continue
            bucket.append(row)
    for key, rows in index.items():
        rows.sort(key=lambda item: int(item.get("priority_score") or 0), reverse=True)
        index[key] = rows
    return index


def _synthesize_planned_queries(
    *,
    category_id: str,
    campus_intent: str,
    question: str,
    limit: int = 4,
) -> list[PlannedQuery]:
    """Build planner phrases from taxonomy when the 50k corpus is not checked in."""
    category = load_taxonomy_categories().get(category_id)
    if category is None:
        return []
    research_intent = research_intent_for_campus(campus_intent)
    preferred: list[str] = []
    for source in sources_for_category(category.category, category.parent_domain):
        domain = (source.get("domain") or "").strip().lower()
        if domain and domain not in preferred:
            preferred.append(domain)
    if category.official_source_url:
        try:
            from urllib.parse import urlparse

            host = (urlparse(category.official_source_url).hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            if host and host not in preferred:
                preferred.insert(0, host)
        except Exception:
            pass
    if "mcneese.edu" not in preferred:
        preferred.append("mcneese.edu")
    domains = tuple(preferred[:6])
    q = (question or "").strip()
    label = category.category.strip() or category.parent_domain.strip() or "McNeese"
    candidates = [
        q,
        f"McNeese {label}",
        f"site:mcneese.edu {label}",
    ]
    if category.subcategories:
        sub = category.subcategories[0][1]
        if sub:
            candidates.append(f"McNeese {sub}")
    planned: list[PlannedQuery] = []
    seen: set[str] = set()
    for idx, query in enumerate(candidates):
        text = " ".join(str(query).split()).strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        planned.append(
            PlannedQuery(
                query_id=f"synth-{category_id}-{idx + 1}",
                query=text[:180],
                intent=research_intent,
                source_mode="official_first",
                preferred_domains=domains,
                answer_schema="",
                freshness_class="weekly",
                priority_score=max(1, 40 - idx * 5),
                risk_level=category.risk_tier or "low",
                seed_entity=label,
            )
        )
        if len(planned) >= limit:
            break
    return planned


def canonical_pack_for_category(category: TaxonomyCategory | TaxonomyMatch | dict[str, Any]) -> str:
    bridge = load_pack_bridge()
    if isinstance(category, TaxonomyCategory):
        name = category.category
        parent = category.parent_domain
    elif isinstance(category, TaxonomyMatch):
        name = category.category
        parent = category.parent_domain
    else:
        name = str(category.get("category") or "")
        parent = str(category.get("parent_domain") or "")
    overrides = bridge.get("category_overrides") or {}
    if name in overrides:
        return str(overrides[name])
    mapping = bridge.get("parent_domain_to_pack") or {}
    return str(mapping.get(parent) or "general_campus")


def research_intent_for_campus(campus_intent: str) -> str:
    bridge = load_pack_bridge()
    return str((bridge.get("campus_intent_to_research") or {}).get(campus_intent) or "official_navigation")


def campus_intent_for_research(research_intent: str) -> str:
    bridge = load_pack_bridge()
    return str((bridge.get("research_intent_to_campus") or {}).get(research_intent) or "explain")


def answer_shape_for_schema(answer_schema: str | None, fallback: str) -> str:
    if not answer_schema:
        return fallback
    bridge = load_pack_bridge()
    mapping = bridge.get("answer_schema_to_shape") or {}
    if answer_schema in mapping:
        return str(mapping[answer_schema])
    # Fuzzy: match by leading field tokens.
    fields = {part.strip() for part in answer_schema.split(",") if part.strip()}
    if {"date", "term", "event_or_requirement"} <= fields or {"date", "timezone", "status"} <= fields:
        return "deadline_card"
    if {"phone", "email", "office"} <= fields:
        return "contact_card"
    if {"apply_url", "employer"} <= fields or "employment_type" in fields:
        return "job_list"
    if {"form_name", "canonical_url"} <= fields:
        return "form_result"
    if {"policy_title", "rule"} <= fields:
        return "policy_plus_steps"
    if {"amount", "currency"} <= fields:
        return "direct_fact"
    if {"building", "map_url"} <= fields or {"location", "hours"} <= fields:
        return "location_card"
    return fallback


def evidence_category_for_shape(answer_shape: str) -> str:
    bridge = load_pack_bridge()
    mapping = bridge.get("schema_evidence_category") or {}
    return str(mapping.get(answer_shape) or "live_discovery")


_EXTRA_CATEGORY_ALIASES = {
    "Campus Dining Services": (
        "meal plan",
        "meal plans",
        "campus dining",
        "dining hall",
        "sodexo",
    ),
    "Campus Housing and Residential Life": (
        "residence life",
        "residence hall",
        "dorm",
        "dorms",
        "on campus housing",
    ),
    "Student Counseling Center": (
        "counseling center",
        "counseling appointment",
        "mental health counseling",
    ),
    "Cashier and Student Accounts": (
        "cashier",
        "cashiers",
        "cashier's office",
        "cashiers office",
        "student accounts",
        "student billing",
    ),
    "Career and Professional Development Center": (
        "career center",
        "career services",
        "professional development center",
    ),
    "Financial Aid": (
        "fafsa",
        "financial aid office",
        "student aid",
    ),
    "University Police, Parking, and IDs": (
        "parking permit",
        "parking pass",
        "campus police",
        "student id card",
    ),
    "Banners Cultural Series": (
        "banners series",
        "banners tickets",
        "banners cultural",
    ),
    "Emergency Status, Closures, and Weather": (
        "emergency closure",
        "campus closed",
        "weather closure",
        "latest emergency update",
    ),
}


def match_taxonomy(question: str) -> TaxonomyMatch | None:
    categories = load_taxonomy_categories()
    if not categories:
        return None
    q = (question or "").strip().lower()
    q_tokens = _tokens(q)
    if not q_tokens:
        return None
    best: TaxonomyMatch | None = None
    for category in categories.values():
        extra = _EXTRA_CATEGORY_ALIASES.get(category.category, ())
        phrases = (category.category, *category.aliases, *extra)
        local_best = 0.0
        hit = ""
        for phrase in phrases:
            normalized = phrase.lower().strip()
            if not normalized:
                continue
            p_tokens = _tokens(normalized)
            if not p_tokens:
                continue
            if normalized in q:
                score = 12.0 + min(len(p_tokens), 5) * 1.8
            else:
                overlap = len(q_tokens & p_tokens)
                if not overlap:
                    continue
                coverage = overlap / max(len(p_tokens), 1)
                # Multi-token phrases need real coverage; single-token office
                # names still count when exact.
                if len(p_tokens) > 1 and coverage < 0.5:
                    continue
                score = overlap * 2.4 + coverage * 3.0
                if coverage >= 0.8:
                    score += 2.0
            if score > local_best:
                local_best, hit = score, phrase
        # Subcategory-only matches still count (meal plans, parking permits…).
        sub_id = None
        sub_name = None
        sub_bonus = 0.0
        for sid, sname in category.subcategories:
            normalized_sub = sname.lower().strip()
            s_tokens = _tokens(normalized_sub)
            if not s_tokens:
                continue
            if normalized_sub in q:
                bonus = 10.0 + min(len(s_tokens), 4)
            else:
                overlap = len(q_tokens & s_tokens)
                coverage = overlap / max(len(s_tokens), 1)
                if not overlap or coverage < 0.5:
                    continue
                bonus = overlap * 2.0 + coverage * 2.5
            if bonus > sub_bonus:
                sub_bonus = bonus
                sub_id, sub_name = sid, sname
                if not hit:
                    hit = sname
        total = local_best + sub_bonus
        if total <= 0:
            continue
        overrides = load_pack_bridge().get("official_url_overrides") or {}
        official_url = str(overrides.get(category.category) or category.official_source_url or "")
        candidate = TaxonomyMatch(
            category_id=category.category_id,
            category=category.category,
            parent_domain=category.parent_domain,
            subcategory_id=sub_id,
            subcategory=sub_name,
            canonical_pack=canonical_pack_for_category(category),
            aliases_hit=hit,
            score=total,
            official_source_url=official_url,
            risk_tier=category.risk_tier,
        )
        if best is None or candidate.score > best.score:
            best = candidate
    if best is None or best.score < 4.0:
        return None
    return best


def plan_corpus_queries(
    *,
    category_id: str | None,
    campus_intent: str,
    question: str,
    limit: int = 6,
) -> list[PlannedQuery]:
    if not category_id:
        return []
    research_intent = research_intent_for_campus(campus_intent)
    rows = list(_query_index().get((category_id, research_intent)) or [])
    if not rows:
        # Fall back to any intent for the category, still priority-sorted.
        for (cid, _intent), bucket in _query_index().items():
            if cid == category_id:
                rows.extend(bucket)
        rows.sort(key=lambda item: int(item.get("priority_score") or 0), reverse=True)
    if not rows:
        # Repo keeps the 50k dump local-only; synthesize from taxonomy so CI and
        # lean deploys still get governed planner phrases.
        return _synthesize_planned_queries(
            category_id=category_id,
            campus_intent=campus_intent,
            question=question,
            limit=limit,
        )
    q_tokens = _tokens(question)
    scored: list[tuple[float, dict[str, str]]] = []
    for row in rows:
        text = (row.get("query") or "").lower()
        seed = (row.get("seed_entity") or "").lower()
        overlap = len(q_tokens & _tokens(f"{text} {seed}"))
        score = float(row.get("priority_score") or 0) + overlap * 4.0
        if seed and seed in (question or "").lower():
            score += 8.0
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    planned: list[PlannedQuery] = []
    seen: set[str] = set()
    for _score, row in scored:
        query = (row.get("query") or "").strip()
        key = query.lower()
        if not query or key in seen:
            continue
        seen.add(key)
        domains = tuple(
            part.strip()
            for part in (row.get("preferred_domains") or "").split("|")
            if part.strip()
        )
        planned.append(
            PlannedQuery(
                query_id=(row.get("query_id") or "").strip(),
                query=query,
                intent=(row.get("intent") or research_intent).strip(),
                source_mode=(row.get("source_mode") or "official_first").strip(),
                preferred_domains=domains,
                answer_schema=(row.get("answer_schema") or "").strip(),
                freshness_class=(row.get("freshness_class") or "weekly").strip().lower(),
                priority_score=int(row.get("priority_score") or 0),
                risk_level=(row.get("risk_level") or "low").strip().lower(),
                seed_entity=(row.get("seed_entity") or "").strip(),
            )
        )
        if len(planned) >= limit:
            break
    return planned


def sources_for_category(category_name: str | None, parent_domain: str | None = None) -> list[dict[str, str]]:
    rows = load_research_source_registry()
    if not rows:
        return []
    needle = " ".join(part for part in (category_name or "", parent_domain or "") if part).lower()
    scored: list[tuple[int, dict[str, str]]] = []
    for row in rows:
        scope = (row.get("category_scope") or "").lower()
        name = (row.get("source_name") or "").lower()
        score = 0
        if "all mcneese" in scope:
            score += 1
        if needle:
            for token in _tokens(needle):
                if token in scope or token in name:
                    score += 2
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], -int(item[1].get("trust_score") or 0)))
    return [row for _score, row in scored[:12]]


def requires_live_discovery(
    *,
    domain: str,
    freshness: str,
    freshness_class: str | None,
    answer_shape: str,
) -> bool:
    bridge = load_pack_bridge()
    if domain in set(bridge.get("live_discovery_domains") or []):
        if freshness in {"live", "current"} or (freshness_class or "") in set(
            bridge.get("live_discovery_freshness_classes") or []
        ):
            return True
    if answer_shape in set(bridge.get("live_discovery_answer_shapes") or []):
        return True
    if (freshness_class or "") in {"hourly", "daily"}:
        return True
    return freshness == "live"


def build_full_spectrum_plan(question: str, *, campus_intent: str) -> FullSpectrumPlan:
    if not pack_available():
        return FullSpectrumPlan(decision_reasons=("full-spectrum pack unavailable",))
    match = match_taxonomy(question)
    if match is None:
        return FullSpectrumPlan(decision_reasons=("no taxonomy category cleared confidence threshold",))
    planned = plan_corpus_queries(
        category_id=match.category_id,
        campus_intent=campus_intent,
        question=question,
        limit=6,
    )
    preferred: list[str] = []
    answer_schema = None
    freshness_class = None
    risk_level = match.risk_tier
    seed_entity = match.category
    research_intent = research_intent_for_campus(campus_intent)
    if planned:
        preferred.extend(planned[0].preferred_domains)
        answer_schema = planned[0].answer_schema
        freshness_class = planned[0].freshness_class
        risk_level = planned[0].risk_level or risk_level
        seed_entity = planned[0].seed_entity or seed_entity
        research_intent = planned[0].intent or research_intent
    sources = sources_for_category(match.category, match.parent_domain)
    for source in sources:
        domain = (source.get("domain") or "").strip().lower()
        if domain and domain not in preferred:
            preferred.append(domain)
    reasons = (
        f"taxonomy matched {match.category_id} ({match.category}) via {match.aliases_hit!r}",
        f"canonical pack {match.canonical_pack} from parent domain {match.parent_domain}",
        f"planned {len(planned)} corpus queries for research intent {research_intent}",
    )
    return FullSpectrumPlan(
        category_id=match.category_id,
        category=match.category,
        parent_domain=match.parent_domain,
        subcategory_id=match.subcategory_id,
        subcategory=match.subcategory,
        canonical_pack=match.canonical_pack,
        match_score=match.score,
        aliases_hit=match.aliases_hit,
        research_intent=research_intent,
        preferred_domains=tuple(dict.fromkeys(preferred)),
        answer_schema=answer_schema,
        freshness_class=freshness_class,
        risk_level=risk_level,
        seed_entity=seed_entity,
        official_source_url=match.official_source_url or None,
        planned_queries=tuple(planned),
        source_policy_ids=tuple(
            (row.get("source_id") or "").strip()
            for row in sources
            if (row.get("source_id") or "").strip()
        ),
        decision_reasons=reasons,
    )


def clear_full_spectrum_caches() -> None:
    load_pack_bridge.cache_clear()
    load_taxonomy_categories.cache_clear()
    load_research_source_registry.cache_clear()
    _query_index.cache_clear()
