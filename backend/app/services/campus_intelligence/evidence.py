"""Domain-intent evidence sufficiency with inspectable field coverage."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Iterable

from .models import CampusQuery, EvidenceSufficiencyResult, ResolvedRoutePolicy
from .registry import get_domain_pack, load_source_group_registry


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
_DATE_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:,\s*\d{4})?\b|\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
    re.I,
)
_CATALOG_YEAR_RE = re.compile(r"\b20\d{2}\s*[-\u2013]\s*20\d{2}\b")
_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.I)


def _tokens(text: str) -> set[str]:
    stop = {"what", "where", "when", "which", "about", "mcneese", "state", "university", "please", "the", "and", "for", "with", "from", "that", "this", "does", "can", "are", "any"}
    return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 2 and token not in stop}


def _evidence_groups(item) -> list[str]:
    explicit = item.metadata.get("source_groups") or item.metadata.get("source_group") or []
    if isinstance(explicit, str):
        explicit = [explicit]
    groups = list(explicit)
    source_id = str(getattr(item, "source_id", "") or "")
    url = str(getattr(item, "url", "") or "")
    for group_id, group in load_source_group_registry()["groups"].items():
        if source_id and source_id in (group.get("source_ids") or []):
            groups.append(group_id)
            continue
        if url and any(url.rstrip("/").lower().startswith(prefix.rstrip("/").lower()) for prefix in (group.get("url_prefixes") or []) if prefix):
            groups.append(group_id)
    return list(dict.fromkeys(groups))


def _field_present(field: str, query: CampusQuery, evidence: list, combined: str) -> bool:
    urls = [str(getattr(item, "url", "") or "") for item in evidence]
    action_links = []
    for item in evidence:
        links = item.metadata.get("action_links") or item.metadata.get("links") or []
        if isinstance(links, list):
            action_links.extend(links)
    has_url = any(url.startswith(("http://", "https://")) for url in urls) or bool(_URL_RE.search(combined))
    has_action = bool(action_links) or bool(re.search(r"\b(?:apply|application|form|download|portal|login|submit)\b", combined, re.I) and has_url)
    # Governed registry pointers (is_link_only) intentionally disclaim knowing
    # changing facts ("destination_only") — they must never be required to
    # carry a freshness timestamp themselves, but they also must not be the
    # *only* evidence that "counts" for recency. Require recency from the
    # substantive (non-pointer) evidence that actually carries the answer.
    substantive_evidence = [item for item in evidence if not getattr(item, "is_link_only", False)] or evidence
    checks = {
        "answer": len(combined.strip()) >= 60,
        "requirements": bool(re.search(r"\brequire|\bmust\b|\bsubmit\b|\beligib", combined, re.I)),
        "audience": query.audience != "unknown" or bool(re.search(r"\bfreshm|\btransfer|\bgraduate|\binternational|\bapplicant", combined, re.I)),
        "application_url": has_action,
        "active_url": has_action,
        "action_link": has_action,
        "authenticated_portal": has_action and query.freshness == "personal",
        "owner": any(getattr(item, "source_tier", "") in {"A", "B"} and getattr(item, "source_name", "") for item in evidence),
        "contact_method": bool(_EMAIL_RE.search(combined) or _PHONE_RE.search(combined)),
        "role": bool(re.search(r"\b(?:office|director|coordinator|registrar|admissions|student central|department|faculty|staff)\b", combined, re.I)),
        "person": bool(re.search(r"\b(?:dr\.?|professor|director|dean|coordinator)\s+[A-Z]", combined)),
        "office": bool(re.search(r"\boffice\b|\bdepartment\b|\bstudent central\b", combined, re.I)),
        "category": bool(query.subdomain or any(_evidence_groups(item) for item in evidence)),
        "categories": bool(any(_evidence_groups(item) for item in evidence)),
        "verified_portal": any(getattr(item, "is_link_only", False) and getattr(item, "url", None) for item in evidence) or has_action,
        "last_verified": (
            any(
                bool(item.metadata.get("last_verified"))
                or item.retrieval_channel in {"official_live", "web_live", "agentic"}
                for item in substantive_evidence
            )
            if substantive_evidence
            else False
        ),
        "deadline": bool(_DATE_RE.search(combined)),
        "date": bool(_DATE_RE.search(combined)),
        "term": bool(query.entities.get("term") or re.search(r"\b(?:spring|summer|fall|winter)\b", combined, re.I)),
        "event": bool(_DATE_RE.search(combined) and len(combined) >= 50),
        "events": bool(_DATE_RE.search(combined)),
        "catalog_year": bool(_CATALOG_YEAR_RE.search(combined)),
        "course": bool(query.entities.get("course") or re.search(r"\b[A-Z]{2,5}\s*\d{3,4}\b", combined)),
        "description": len(combined.strip()) >= 80,
        "credits": bool(re.search(r"\b(?:credit|cr:)\s*\d|\d\s*(?:credit hours?|credits?)\b", combined, re.I)),
        "prerequisites": bool(re.search(r"\bprerequisite", combined, re.I)),
        "program": bool(query.entities.get("program") or re.search(r"\b(?:program|degree|concentration|major)\b", combined, re.I)),
        "programs": bool(re.search(r"\b(?:programs?|degrees?|majors?)\b", combined, re.I)),
        "policy": bool(re.search(r"\b(?:policy|suspension|probation|appeal|procedure)\b", combined, re.I)),
        "steps": bool(re.search(r"(?:^|\n)(?:\d+[.)]|[-*])\s+", combined) or re.search(r"\b(?:first|next|then|submit|complete|contact)\b", combined, re.I)),
        "effective_information": bool(re.search(r"\b(?:effective|revised|approved|catalog year|20\d{2})\b", combined, re.I)),
        "content_type": any(bool(item.metadata.get("content_type")) for item in evidence) or any(url.lower().split("?")[0].endswith((".pdf", ".doc", ".docx")) for url in urls),
        "form": bool(query.entities.get("form") or re.search(r"\bform\b", combined, re.I)),
        "records": bool(evidence),
        "courses": bool(re.search(r"\b[A-Z]{2,5}\s*\d{3,4}\b", combined)),
        "location": bool(re.search(r"\b(?:building|hall|room|street|avenue|drive|location|campus map)\b", combined, re.I)),
        "place": bool(re.search(r"\b(?:building|hall|room|street|avenue|drive|location)\b", combined, re.I)),
        "address_or_map": bool(re.search(r"\b\d{2,5}\s+[A-Z][A-Za-z ]+\b|\bmap\b", combined)),
        "services": len(combined.strip()) >= 80,
        "official_guidance": bool(evidence),
        "opportunities_or_portals": has_action,
        "availability": bool(re.search(r"\b(?:available|open|closed|hours?|no .*found)\b", combined, re.I)),
        "status": bool(re.search(r"\b(?:open|closed|status|alert|cancel)\b", combined, re.I)),
        "escalation_contact": bool(_EMAIL_RE.search(combined) or _PHONE_RE.search(combined)),
        "amount_or_method": bool(re.search(r"\$\s*\d|\b(?:pay|payment|tuition|fees?)\b", combined, re.I)),
        "official_rates": bool(re.search(r"\$\s*\d|\bper (?:credit|semester|term)\b", combined, re.I)),
        "inputs": bool(query.entities),
        "qualification": bool(re.search(r"\b(?:may|depends|estimate|official|verify|eligible|require)\b", combined, re.I)),
        "activity_or_status": bool(re.search(r"\b(?:active|event|meeting|status|join)\b", combined, re.I)),
        "organization": bool(re.search(r"\b(?:organization|club|association|society)\b", combined, re.I)),
        "organizations": bool(re.search(r"\b(?:organizations|clubs|associations|societies)\b", combined, re.I)),
        "verified_profile": has_url,
        "requirements_checklist": bool(evidence),
        "enabled_domain_packs": True,
        "active_routes": True,
        "limitations": True,
        "examples": True,
        "trust_tiers": True,
    }
    return bool(checks.get(field, bool(evidence and len(combined.strip()) >= 40)))


def evaluate_evidence(
    query: CampusQuery,
    evidence: Iterable,
    *,
    policy: ResolvedRoutePolicy | None = None,
) -> EvidenceSufficiencyResult:
    items = list(evidence)
    query_terms = _tokens(query.normalized_query) | _tokens(query.domain.replace("_", " "))
    accepted = []
    rejected: list[dict[str, str]] = []
    for item in items:
        text = f"{getattr(item, 'title', '')} {getattr(item, 'text', '')} {getattr(item, 'category', '')}"
        evidence_terms = _tokens(text)
        overlap = query_terms & evidence_terms
        groups = _evidence_groups(item)
        group_match = bool(set(groups) & set(query.required_source_groups))
        # Source-group ownership can establish relevance for concise link records.
        relevant = bool(overlap or group_match)
        if query.domain == "capability_discovery":
            relevant = False
        if relevant:
            item.metadata["source_groups"] = groups
            accepted.append(item)
        else:
            rejected.append({
                "evidence_id": str(getattr(item, "evidence_id", "")),
                "reason": "no query-term or required-source-group match",
            })
    combined = "\n".join(
        f"{getattr(item, 'title', '')}\n{getattr(item, 'text', '')}\n{getattr(item, 'url', '') or ''}"
        for item in accepted
    )
    coverage = {
        field: _field_present(field, query, accepted, combined)
        for field in query.required_fields
    }
    missing_fields = [field for field, present in coverage.items() if not present]
    covered_groups = sorted({group for item in accepted for group in _evidence_groups(item)})
    missing_groups = [] if set(covered_groups) & set(query.required_source_groups) else list(query.required_source_groups)
    pack = get_domain_pack(query.domain) or {}
    intent_defaults = (pack.get("intent_defaults") or {}).get(query.intent) or {}
    action_required = bool(intent_defaults.get("action_link_required"))
    if action_required and not any(coverage.get(field) for field in ("active_url", "application_url", "action_link", "verified_portal")):
        if "ACTION_LINK_INVALID" not in missing_fields:
            missing_fields.append("active_action_link")
    relevant_ratio = len(accepted) / max(len(items), 1)
    field_ratio = sum(coverage.values()) / max(len(coverage), 1)
    source_ratio = 1.0 if not query.required_source_groups or not missing_groups else 0.0
    score = round(0.40 * field_ratio + 0.35 * source_ratio + 0.25 * relevant_ratio, 3)
    partial_allowed = bool(
        (
            query.domain == "employment"
            or getattr(query, "requires_live_discovery", False)
            or query.answer_shape
            in {
                "job_list",
                "event_list",
                "calendar_list",
                "categorized_list",
                "precise_partial",
                "action_link_result",
            }
        )
        and any(
            coverage.get(field)
            for field in (
                "verified_portal",
                "application_url",
                "active_url",
                "action_link",
                "events",
                "opportunities_or_portals",
            )
        )
    )
    passed = bool(accepted and not missing_groups and not missing_fields)
    failure_codes: list[str] = []
    if not accepted:
        failure_codes.append("NO_MATCHING_RECORDS")
    if missing_groups:
        failure_codes.append("SOURCE_GROUP_NOT_CONFIGURED" if not items else "EVIDENCE_BELOW_THRESHOLD")
    if missing_fields:
        failure_codes.append("INSUFFICIENT_FIELD_COVERAGE")
    if query.freshness == "personal":
        passed = False
        failure_codes = ["PERSONAL_DATA_REQUIRED"]
    next_route = None
    if policy:
        for channel in policy.precedence:
            decision = policy.channels.get(channel)
            if decision and decision.state in {"FALLBACK", "CONDITIONAL", "PRIMARY", "REQUIRED"}:
                next_route = channel
                break
    return EvidenceSufficiencyResult(
        passed=passed,
        score=score,
        required_fields=list(query.required_fields),
        field_coverage=coverage,
        missing_fields=missing_fields,
        covered_source_groups=covered_groups,
        missing_source_groups=missing_groups,
        accepted_evidence_ids=[str(getattr(item, "evidence_id", "")) for item in accepted],
        rejected_evidence=rejected,
        failure_codes=list(dict.fromkeys(failure_codes)),
        next_permitted_route=next_route,
        partial_allowed=partial_allowed,
    )

