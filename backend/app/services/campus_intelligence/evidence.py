"""Domain-intent evidence sufficiency with inspectable field coverage."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Any, Iterable

from .models import (
    CampusQuery,
    EvidenceContradiction,
    EvidenceSufficiencyResult,
    FactResolution,
    ResolvedRoutePolicy,
)
from .registry import get_domain_pack, load_source_group_registry


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
_DATE_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:,\s*\d{4})?\b|\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
    re.I,
)
_START_EVENT_RE = re.compile(
    r"\b(?:classes?\s+begin|instruction\s+begins?|first\s+day|"
    r"semester\s+starts?|term\s+starts?|begins?(?:\s+on)?|starts?(?:\s+on)?)\b",
    re.I,
)
_NAMED_PLACE_RE = re.compile(
    r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4}\s+"
    r"(?:Library|Hall|Center|Building|Union|Complex|Theatre|Theater))\b"
)
_LOCATED_AT_RE = re.compile(
    r"\blocated (?:in|at|on)\s+([^.;\n]{8,90})",
    re.I,
)
_CATALOG_YEAR_RE = re.compile(r"\b20\d{2}\s*[-\u2013]\s*20\d{2}\b")
_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.I)
_MONEY_RE = re.compile(r"\$\s*\d+(?:\.\d{2})?", re.I)
_ADDRESS_RE = re.compile(
    r"\b\d{3,5}\s+[A-Z][A-Za-z0-9 .'-]{1,70}?"
    r"(?:Street|St\.?|Road|Rd\.?|Drive|Dr\.?|Avenue|Ave\.?)\b"
)
_TIME_RANGE_RE = re.compile(
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
    r"Mon(?:day)?|Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Fri(?:day)?|"
    r"Sat(?:urday)?|Sun(?:day)?)(?:\s*[-â€“]\s*(?:Monday|Tuesday|Wednesday|"
    r"Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun))?"
    r"[^.;\n]{0,100}\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)"
    r"[^.;\n]{0,40}",
    re.I,
)

_EXACT_VALUE_FIELDS = {
    "active_url",
    "action_link",
    "address_or_map",
    "application_url",
    "contact_method",
    "date",
    "deadline",
    "hours",
    "location",
    "replacement_fee",
    "replacement_location",
    "verified_portal",
}
_SINGLE_VALUE_FIELDS = {
    "date",
    "deadline",
    "location",
    "replacement_fee",
    "replacement_location",
}


def _tokens(text: str) -> set[str]:
    stop = {
        "what", "where", "when", "which", "about", "mcneese", "state",
        "university", "campus", "general", "information", "official", "please",
        "the", "and", "for", "with", "from", "that", "this", "does", "can",
        "are", "any",
    }
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


def _normalize_value(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n.,;:")
    if text.startswith("$"):
        return "$" + re.sub(r"[^0-9.]", "", text)
    if _PHONE_RE.fullmatch(text):
        digits = re.sub(r"\D", "", text)
        return digits[-10:]
    return text.casefold()


def _metadata_values(item, field: str) -> list[str]:
    values: list[str] = []
    facts = getattr(item, "facts", None) or {}
    raw = facts.get(field)
    if raw is not None:
        values.extend(raw if isinstance(raw, list) else [raw])
    metadata = getattr(item, "metadata", None) or {}
    resolved = metadata.get("resolved_facts") or {}
    raw = resolved.get(field)
    if isinstance(raw, dict):
        raw = raw.get("value") if "value" in raw else raw.get("values")
    if raw is not None:
        values.extend(raw if isinstance(raw, list) else [raw])
    return [str(value).strip() for value in values if str(value).strip()]


def _extract_field_values(field: str, query: CampusQuery, item) -> list[str]:
    explicit = _metadata_values(item, field)
    if explicit:
        return explicit
    text = str(getattr(item, "text", "") or "")
    metadata = getattr(item, "metadata", None) or {}
    values: list[str] = []
    if field in {"contact_method", "escalation_contact"}:
        values.extend(_EMAIL_RE.findall(text))
        values.extend(match.group(0) for match in _PHONE_RE.finditer(text))
    elif field in {"deadline", "date"}:
        dates = [match.group(0) for match in _DATE_RE.finditer(text)]
        query_text = str(query.normalized_query or "")
        wants_start = bool(
            re.search(r"\b(?:start|begin|first day)\b", query_text, re.I)
        ) and not re.search(r"\b(?:deadline|withdraw|drop|last day)\b", query_text, re.I)
        if wants_start:
            contextual: list[str] = []
            for match in _DATE_RE.finditer(text):
                window = text[max(0, match.start() - 90): min(len(text), match.end() + 90)]
                if _START_EVENT_RE.search(window):
                    contextual.append(match.group(0))
            values.extend(contextual)
        else:
            values.extend(dates)
    elif field in {"replacement_fee", "amount_or_method", "official_rates"}:
        values.extend(match.group(0) for match in _MONEY_RE.finditer(text))
    elif field in {"location", "replacement_location", "place", "address_or_map"}:
        values.extend(match.group(0) for match in _ADDRESS_RE.finditer(text))
        values.extend(match.group(0) for match in _NAMED_PLACE_RE.finditer(text))
        located = _LOCATED_AT_RE.search(text)
        if located:
            values.append(located.group(1).strip())
        if field == "place":
            title = str(getattr(item, "title", "") or "")
            named_title = _NAMED_PLACE_RE.search(title)
            if named_title:
                values.append(named_title.group(0))
    elif field == "hours":
        values.extend(match.group(0).strip() for match in _TIME_RANGE_RE.finditer(text))
    elif field in {"application_url", "active_url", "action_link", "verified_portal"}:
        links = metadata.get("action_links") or metadata.get("links") or []
        for link in links if isinstance(links, list) else []:
            if isinstance(link, dict) and link.get("url"):
                values.append(str(link["url"]))
            elif isinstance(link, str):
                values.append(link)
        if not values and getattr(item, "url", None):
            values.append(str(item.url))
    elif field in {"term", "subject", "constraint_course", "course_query"}:
        # Query entities become evidence-backed only when a structured specialist
        # executed against an authoritative dataset for this request.
        if metadata.get("structured_execution"):
            entity_key = {
                "term": "term",
                "subject": "subject",
                "constraint_course": "constraint_course",
                "course_query": "course_query",
            }[field]
            entity_value = query.entities.get(entity_key)
            if entity_value:
                values.append(str(entity_value))
    return list(dict.fromkeys(value for value in values if value))


def _field_mentioned(field: str, text: str) -> bool:
    aliases = {
        "replacement_fee": r"\b(?:replacement|replace).{0,80}\b(?:fee|charge|cost)\b|\b(?:fee|charge|cost)\b",
        "replacement_location": r"\b(?:replace|replacement|pick\s*up|office|location|address)\b",
        "deadline": r"\b(?:deadline|last\s+date|last\s+day|due|within\s+\d+\s+days?)\b",
        "date": r"\b(?:date|day|term|semester)\b",
        "contact_method": r"\b(?:contact|phone|email|call)\b",
        "hours": r"\b(?:hours?|open|closed|closing)\b",
        "location": r"\b(?:location|located|address|office|building|room)\b",
        "application_url": r"\b(?:apply|application|form|portal|submit)\b",
        "active_url": r"\b(?:apply|application|form|portal|submit)\b",
        "action_link": r"\b(?:apply|application|form|portal|submit)\b",
        "verified_portal": r"\b(?:portal|login|sign\s*in)\b",
    }
    pattern = aliases.get(field)
    return bool(pattern and re.search(pattern, text, re.I | re.S))


def _resolve_fields(
    query: CampusQuery,
    evidence: list,
    combined: str,
) -> tuple[dict[str, FactResolution], list[EvidenceContradiction]]:
    resolutions: dict[str, FactResolution] = {}
    contradictions: list[EvidenceContradiction] = []
    support_count_by_id: dict[str, int] = {}
    for item in evidence:
        evidence_id = str(getattr(item, "evidence_id", "") or "")
        item_text = str(getattr(item, "text", "") or "")
        support_count_by_id[evidence_id] = sum(
            1
            for required_field in query.required_fields
            if _extract_field_values(required_field, query, item)
            or (
                required_field not in _EXACT_VALUE_FIELDS
                and _field_present(required_field, query, [item], item_text)
            )
        )
    for field in query.required_fields:
        values_by_normalized: dict[str, list[tuple[str, str]]] = {}
        mentioned_ids: list[str] = []
        for item in evidence:
            evidence_id = str(getattr(item, "evidence_id", "") or "")
            item_text = str(getattr(item, "text", "") or "")
            values = _extract_field_values(field, query, item)
            if values:
                for value in values:
                    normalized = _normalize_value(value)
                    if normalized:
                        values_by_normalized.setdefault(normalized, []).append((value, evidence_id))
            elif _field_mentioned(field, item_text):
                mentioned_ids.append(evidence_id)

        if field not in _EXACT_VALUE_FIELDS and not values_by_normalized:
            supporting = [
                str(getattr(item, "evidence_id", "") or "")
                for item in evidence
                if _field_present(field, query, [item], str(getattr(item, "text", "") or ""))
            ]
            if supporting:
                values_by_normalized["true"] = [("true", evidence_id) for evidence_id in supporting]

        normalized_values = list(values_by_normalized)
        if field in _SINGLE_VALUE_FIELDS and len(normalized_values) > 1:
            mapping = {
                normalized: list(dict.fromkeys(evidence_id for _, evidence_id in pairs if evidence_id))
                for normalized, pairs in values_by_normalized.items()
            }
            unique_ids = {
                evidence_id
                for evidence_ids in mapping.values()
                for evidence_id in evidence_ids
            }
            page_read_ids = {
                str(getattr(item, "evidence_id", "") or "")
                for item in evidence
                if (getattr(item, "metadata", None) or {}).get("page_read")
                or (getattr(item, "metadata", None) or {}).get("page_fetched")
            }
            if page_read_ids and unique_ids - page_read_ids:
                live_values: dict[str, list[tuple[str, str]]] = {}
                for normalized, pairs in values_by_normalized.items():
                    live_pairs = [(value, evidence_id) for value, evidence_id in pairs if evidence_id in page_read_ids]
                    if live_pairs:
                        live_values[normalized] = live_pairs
                if live_values:
                    values_by_normalized = live_values
                    normalized_values = list(values_by_normalized)
                    mapping = {
                        normalized: list(dict.fromkeys(evidence_id for _, evidence_id in pairs if evidence_id))
                        for normalized, pairs in values_by_normalized.items()
                    }
                    unique_ids = {
                        evidence_id
                        for evidence_ids in mapping.values()
                        for evidence_id in evidence_ids
                    }
                    if len(normalized_values) <= 1:
                        # Live page text resolved the field; index snippets are not a conflict.
                        pass
            if len(normalized_values) > 1:
                same_page_calendar = (
                    field in {"date", "deadline"}
                    and len(unique_ids) <= 1
                )
                if not same_page_calendar:
                    contradiction = EvidenceContradiction(
                        field=field,
                        values=normalized_values,
                        evidence_ids_by_value=mapping,
                    )
                    contradictions.append(contradiction)
                    resolutions[field] = FactResolution(
                        field=field,
                        status="CONFLICTED",
                        normalized_values=normalized_values,
                        evidence_ids=list(dict.fromkeys(eid for ids in mapping.values() for eid in ids)),
                        mentioned_evidence_ids=list(dict.fromkeys(mentioned_ids)),
                    )
                    continue

        if normalized_values:
            display_values = [values_by_normalized[value][0][0] for value in normalized_values]
            strength_by_id = {
                str(getattr(item, "evidence_id", "") or ""): (
                    support_count_by_id.get(
                        str(getattr(item, "evidence_id", "") or ""), 0
                    ),
                    float(getattr(item, "relevance_score", 0.0) or 0.0),
                )
                for item in evidence
            }
            strongest_pairs: list[tuple[str, str]] = []
            for pairs in values_by_normalized.values():
                scored = [
                    (value, evidence_id, strength_by_id.get(evidence_id, (0, 0.0)))
                    for value, evidence_id in pairs
                    if evidence_id
                ]
                if not scored:
                    continue
                strongest_score = max(score for _, _, score in scored)
                strongest_pairs.extend(
                    (value, evidence_id)
                    for value, evidence_id, score in scored
                    if score == strongest_score
                )
            evidence_ids = list(dict.fromkeys(
                evidence_id
                for _, evidence_id in strongest_pairs
                if evidence_id
            ))
            tiers = {
                str(getattr(item, "source_tier", "") or "")
                for item in evidence
                if str(getattr(item, "evidence_id", "") or "") in evidence_ids
            }
            verified = [
                str((getattr(item, "metadata", None) or {}).get("last_verified") or "")
                for item in evidence
                if str(getattr(item, "evidence_id", "") or "") in evidence_ids
            ]
            resolutions[field] = FactResolution(
                field=field,
                status="RESOLVED",
                value=display_values[0] if len(display_values) == 1 else display_values,
                normalized_values=normalized_values,
                evidence_ids=evidence_ids,
                mentioned_evidence_ids=list(dict.fromkeys(mentioned_ids)),
                authority="official" if tiers.intersection({"A", "B"}) else "context",
                last_verified=max((value for value in verified if value), default=None),
            )
        elif mentioned_ids:
            resolutions[field] = FactResolution(
                field=field,
                status="MENTIONED_UNRESOLVED",
                mentioned_evidence_ids=list(dict.fromkeys(mentioned_ids)),
            )
        else:
            resolutions[field] = FactResolution(field=field, status="MISSING")
    return resolutions, contradictions


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
        "answer": (
            len(combined.strip()) >= 60
            and any(
                not getattr(item, "is_link_only", False)
                and len(str(getattr(item, "text", "") or "").strip()) >= 60
                for item in evidence
            )
            and bool(
                _tokens(combined)
                & (
                    _tokens(query.normalized_query)
                    | _tokens(query.domain.replace("_", " "))
                )
            )
        ),
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
        "subject": bool(query.entities.get("subject") or re.search(r"\b[A-Z]{2,5}\b", combined)),
        "course_query": bool(query.entities.get("course_query")),
        "constraint_course": bool(query.entities.get("constraint_course")),
        "courses": bool(
            re.search(r"\b[A-Z]{2,5}\s*\d{3,4}\b", combined)
            or re.search(r"\bno courses matching\b", combined, re.I)
            or re.search(r"\bno validated class search dataset\b", combined, re.I)
        ),
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
        "location": bool(re.search(r"\b(?:building|hall|room|street|avenue|drive|location|campus map)\b", combined, re.I)),
        "hours": bool(re.search(r"\b(?:hours?|open|closed)\b.*\b(?:a\.?m\.?|p\.?m\.?|monday|tuesday|wednesday|thursday|friday|weekday)\b|\b(?:monday|tuesday|wednesday|thursday|friday)\b.*\b(?:hours?|open|closed|a\.?m\.?|p\.?m\.?)\b", combined, re.I)),
        "place": bool(re.search(r"\b(?:building|hall|room|street|avenue|drive|location)\b", combined, re.I)),
        "address_or_map": bool(re.search(r"\b\d{2,5}\s+[A-Z][A-Za-z ]+\b|\bmap\b", combined)),
        "services": len(combined.strip()) >= 80,
        "official_guidance": bool(evidence),
        "opportunities_or_portals": has_action,
        "availability": bool(re.search(r"\b(?:available|open|closed|hours?|no .*found)\b", combined, re.I)),
        "status": bool(re.search(r"\b(?:open|closed|status|alert|cancel)\b", combined, re.I)),
        "escalation_contact": bool(_EMAIL_RE.search(combined) or _PHONE_RE.search(combined)),
        "amount_or_method": bool(re.search(r"\$\s*\d|\b(?:pay|payment|tuition|fees?)\b", combined, re.I)),
        "replacement_process": bool(
            re.search(r"\b(?:id|identification)\s+card\b", combined, re.I)
            and re.search(r"\b(?:form|submit|request|replace|replacement)\b", combined, re.I)
        ),
        "replacement_location": bool(
            re.search(r"\b\d{3,5}\s+[A-Z][A-Za-z .'-]+(?:Street|St\.?|Road|Rd\.?|Drive|Dr\.?)\b", combined)
            or re.search(r"\b(?:university police|student central)\b.{0,120}\b(?:location|address|hall|street|drive)\b", combined, re.I | re.S)
        ),
        "replacement_fee": bool(re.search(r"\$\s*\d+(?:\.\d{2})?\s*(?:fee|charge)?|\b(?:fee|charge)\s+(?:is\s+)?\$\s*\d+", combined, re.I)),
        "advisor_identification_steps": bool(
            re.search(r"\b(?:advisor|advising)\b", combined, re.I)
            and re.search(r"\bbanner\s*9\b", combined, re.I)
            and re.search(r"\bstudent\s+profile\b", combined, re.I)
        ),
        "resolution_options": bool(
            re.search(
                r"\b(?:drop|change|switch|override|resolve|options?|"
                r"different\s+(?:course|class|section)|choose\s+(?:a\s+)?different|section)\b",
                combined,
                re.I,
            )
        ),
        "emergency_guidance": bool(re.search(r"\b(?:911|9-1-1|emergency room|university police)\b", combined, re.I)),
        "current_student_guidance": bool(
            re.search(r"\bcurrent international students?\b", combined, re.I)
            and re.search(r"\b(?:guide|visa status|contact|international student services)\b", combined, re.I)
        ),
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


_ENTITY_GENERIC_TERMS = {
    "campus", "contact", "department", "hours", "international", "mcneese",
    "office", "services", "state", "student", "students", "university",
}


def _requested_entity_terms(query: CampusQuery) -> set[str]:
    """Return the distinctive identity for office/contact operations."""
    if query.intent not in {"find_contact", "locate", "identify_office", "navigate"}:
        return set()
    target = (
        getattr(query, "seed_entity", None)
        or getattr(query, "category", None)
        or query.entities.get("office")
        or query.entities.get("location")
        or ""
    )
    terms = _tokens(str(target)) - _ENTITY_GENERIC_TERMS
    # "International" is generic only in the broad stop set above; for the
    # International Student Services entity it is the distinctive identity.
    if "international" in _tokens(str(target)):
        terms.add("international")
    return terms


def _evidence_identity_terms(item) -> set[str]:
    metadata = getattr(item, "metadata", None) or {}
    structured = metadata.get("structured_result") or {}
    url_path = urlparse(str(getattr(item, "url", "") or "")).path.replace("-", " ")
    return _tokens(
        " ".join((
            str(getattr(item, "title", "") or ""),
            str(getattr(item, "source_name", "") or ""),
            str(structured.get("title") or ""),
            url_path,
        ))
    )


def _evidence_contains_requested_course(query: CampusQuery, item) -> bool:
    course = str(query.entities.get("course") or "").strip()
    match = re.fullmatch(r"([A-Z]{2,5})\s*(\d{3,4}[A-Z]?)", course, re.I)
    if not match:
        return True
    subject, number = match.groups()
    blob = " ".join((
        str(getattr(item, "title", "") or ""),
        str(getattr(item, "text", "") or ""),
        urlparse(str(getattr(item, "url", "") or "")).path.replace("-", " "),
    ))
    return bool(re.search(
        rf"\b{re.escape(subject)}\s*[- ]?\s*{re.escape(number)}\b",
        blob,
        re.I,
    ))


def evaluate_evidence(
    query: CampusQuery,
    evidence: Iterable,
    *,
    policy: ResolvedRoutePolicy | None = None,
) -> EvidenceSufficiencyResult:
    items = list(evidence)
    query_terms = _tokens(query.normalized_query) | _tokens(query.domain.replace("_", " "))
    requested_item = str(query.entities.get("item") or "").strip()
    item_terms = _tokens(requested_item)
    requested_entity_terms = _requested_entity_terms(query)
    accepted = []
    rejected: list[dict[str, str]] = []
    strict_source_groups = {
        "academic_advising",
        "health_services",
        "international_services",
        "official_calendar",
        "parking_transportation",
        "student_id_cards",
    }
    require_group_match = bool(set(query.required_source_groups) & strict_source_groups)
    for item in items:
        text = f"{getattr(item, 'title', '')} {getattr(item, 'text', '')} {getattr(item, 'category', '')}"
        evidence_terms = _tokens(text)
        overlap = query_terms & evidence_terms
        groups = _evidence_groups(item)
        group_match = bool(set(groups) & set(query.required_source_groups))
        page_read = bool(
            (getattr(item, "metadata", None) or {}).get("page_read")
            or (getattr(item, "metadata", None) or {}).get("page_fetched")
        ) and len(str(getattr(item, "text", "") or "").strip()) >= 80
        # A broad source-group label is not semantic proof. Non-specialist
        # evidence must match both the governed group and the user's subject.
        # Curated specialist groups can establish relevance by exact ownership.
        relevant = (
            group_match
            if require_group_match
            else bool(overlap and (group_match or not groups))
        )
        if (
            getattr(item, "retrieval_channel", "") == "kb"
            and overlap
            and (not require_group_match or group_match)
        ):
            relevant = True
        # A successfully read official page that overlaps the question still
        # counts when the registry assigned a neighboring source group.
        if page_read and overlap:
            relevant = True
        if requested_entity_terms:
            identity = _evidence_identity_terms(item) | evidence_terms
            matched = requested_entity_terms.intersection(identity)
            if not matched:
                matched = {
                    term
                    for term in requested_entity_terms
                    for other in identity
                    if min(len(term), len(other)) >= 5
                    and (term.startswith(other) or other.startswith(term))
                }
            relevant = bool(relevant and matched)
        if query.entities.get("course"):
            relevant = bool(relevant and _evidence_contains_requested_course(query, item))
        if query.domain == "student_services" and query.subdomain == "bookstore" and item_terms:
            # A named-book search must match the distinctive requested title,
            # while a governed bookstore pointer may remain as a useful next step.
            # The generic word "book" alone cannot admit unrelated readings,
            # literature programs, or adoption-form pages.
            destination_url = str(getattr(item, "url", "") or "").lower().rstrip("/")
            bookstore_roots = {
                "https://www.mcneese.edu/bookstore",
                "https://www.mcneese.edu/bookstore-2",
                "https://mcneesecowboystore.com",
                "https://mcneesecowboystore.com/home",
                "https://www.mcneesecowboystore.com",
                "https://www.mcneesecowboystore.com/home",
            }
            governed_destination = bool(
                group_match and getattr(item, "is_link_only", False)
                and destination_url in bookstore_roots
            )
            relevant = bool(item_terms & evidence_terms or governed_destination)
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
    resolutions, contradictions = _resolve_fields(query, accepted, combined)
    coverage = {
        field: resolution.status == "RESOLVED"
        for field, resolution in resolutions.items()
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
    if (
        not contradictions
        and requested_entity_terms
        and query.intent in {"find_contact", "locate", "identify_office", "navigate"}
        and accepted
        and any(coverage.get(field) for field in ("location", "hours", "contact_method", "place"))
        and set(missing_fields).issubset({"location", "hours", "contact_method", "role", "place", "address_or_map"})
    ):
        # Release a precise answer for the exact named entity when only one
        # requested operational field remains unpublished. Never substitute a
        # different office's facts to manufacture completeness.
        partial_allowed = True
    if (
        not contradictions
        and query.intent in {"find_contact", "locate", "identify_office"}
        and any(
            bool((getattr(item, "metadata", None) or {}).get("page_read")
                 or (getattr(item, "metadata", None) or {}).get("page_fetched"))
            and len(str(getattr(item, "text", "") or "").strip()) >= 120
            and "Governed campus source record" not in str(getattr(item, "text", "") or "")
            for item in accepted
        )
    ):
        # Claude can extract remaining fields from a successfully opened official page.
        partial_allowed = True
    passed = bool(accepted and not missing_groups and not missing_fields and not contradictions)
    failure_codes: list[str] = []
    if not accepted:
        failure_codes.append("NO_MATCHING_RECORDS")
    if missing_groups:
        failure_codes.append("SOURCE_GROUP_NOT_CONFIGURED" if not items else "EVIDENCE_BELOW_THRESHOLD")
    if missing_fields:
        failure_codes.append("INSUFFICIENT_FIELD_COVERAGE")
    if contradictions:
        failure_codes.append("EVIDENCE_CONFLICT")
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
        field_resolutions={key: value.to_dict() for key, value in resolutions.items()},
        contradictions=[item.to_dict() for item in contradictions],
    )

