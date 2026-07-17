"""Deterministic retrieval classifier for RCCS.

Domain-general within AskMcNeese. Example entities (faculty names, org
abbreviations) are not hardcoded product boundaries — aliases come from
registry data and lightweight pattern extraction.
"""

from __future__ import annotations

import re
from dataclasses import replace

from app.services.rccs.models import DetectedEntity, RetrievalClassification

# Intent labels (stable string constants for plans/tests)
INTENT_FACULTY_IDENTITY = "faculty_identity"
INTENT_FACULTY_RATINGS = "faculty_ratings"
INTENT_ORG_IDENTITY = "organization_identity"
INTENT_ORG_ACTIVITY = "organization_activity"
INTENT_SOCIAL_PROFILE = "social_profile"
INTENT_ADMISSIONS_POLICY = "admissions_policy"
INTENT_EVENTS_CURRENT = "events_current"
INTENT_ATHLETICS = "athletics"
INTENT_CAMPUS_SERVICES = "campus_services"
INTENT_ACADEMIC_PROGRAMS = "academic_programs"
INTENT_TERM_DEFINITION = "term_definition"
INTENT_GENERAL = "general_campus"

_TITLE_RE = re.compile(
    r"\b(?:dr\.?|doctor|professor|prof\.?|dean|coach|instructor)\s+",
    re.IGNORECASE,
)

_FACULTY_IDENTITY_CUES = [
    r"\bwho is\b",
    r"\bwhat department\b",
    r"\bcontact\b",
    r"\bemail\b",
    r"\boffice hours\b",
    r"\bfaculty\b",
    r"\bstaff\b",
    r"\binstructor\b",
]

_RATING_CUES = [
    r"\brate(?:d|s|ing)?\b",
    r"\brating\b",
    r"\brate my professor\b",
    r"\brmp\b",
    r"\bstudents (?:say|think|feel)\b",
    r"\bstudent (?:opinion|review|reviews|feedback)\b",
    r"\bdifficult(?:y)?\b",
    r"\bwould take again\b",
    r"\breputation\b",
    r"\breviews?\b",
]

_ORG_CUES = [
    r"\borganization\b",
    r"\borg\b",
    r"\bclub\b",
    r"\bclubs\b",
    r"\bstudent (?:org|organization|association|group)\b",
    r"\bassociation\b",
    r"\bwhat is\b.+\bat mcneese\b",
    r"\bget involved\b",
    r"\bpresence\b",
]

_ACTIVITY_CUES = [
    r"\bwhat(?:'s| is) going on\b",
    r"\brecent(?:ly)?\b",
    r"\blatest\b",
    r"\bactive\b",
    r"\bup to\b",
    r"\bevents?\b",
    r"\bannouncements?\b",
    r"\bhappening\b",
    r"\bdoing (?:lately|recently)\b",
]

_SOCIAL_CUES = [
    r"\binstagram\b",
    r"\blinkedin\b",
    r"\btwitter\b",
    r"\bx\.com\b",
    r"\bfacebook\b",
    r"\bsocial(?: media)?\b",
    r"\bprofile\b",
    r"\bfollow\b",
]

_FRESHNESS_CUES = [
    r"\bcurrent(?:ly)?\b",
    r"\btoday\b",
    r"\brecent(?:ly)?\b",
    r"\blatest\b",
    r"\bwhat(?:'s| is) going on\b",
    r"\bupcoming\b",
    r"\bthis semester\b",
    r"\bnow\b",
    r"\bactive\b",
    r"\bevents?\b",
    r"\bannouncements?\b",
    r"\bhours?\b",
]

_ADMISSIONS_CUES = [
    r"\badmission",
    r"\btuition\b",
    r"\bdeadline\b",
    r"\bfafsa\b",
    r"\bscholarship",
    r"\bfinancial aid\b",
    r"\bapply\b",
    r"\bpolicy\b",
    r"\bpolicies\b",
    r"\bcatalog\b",
    r"\brequirement",
]

_ATHLETICS_CUES = [
    r"\bathletics?\b",
    r"\bsports?\b",
    r"\bcowboys?\b",
    r"\bcowgirls?\b",
    r"\bfootball\b",
    r"\bbasketball\b",
    r"\btickets?\b",
    r"\bgame\b",
]

_SERVICES_CUES = [
    r"\blibrary\b",
    r"\bhousing\b",
    r"\bdining\b",
    r"\badvising\b",
    r"\bregistrar\b",
    r"\binternational\b",
    r"\bstudent central\b",
    r"\bparking\b",
    r"\bmap\b",
    r"\bhours?\b",
]

_PROGRAM_CUES = [
    r"\bmajor\b",
    r"\bprogram\b",
    r"\bdegree\b",
    r"\bcomputer science\b",
    r"\bnursing\b",
    r"\bengineering\b",
    r"\bundergraduate\b",
    r"\bgraduate\b",
]

_FACULTY_NAME_RE = re.compile(
    r"(?:dr\.?|doctor|professor|prof\.?|dean|coach|instructor)\s+"
    r"([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?)",
    re.IGNORECASE,
)

_WHO_IS_RE = re.compile(
    r"who is\s+(?:dr\.?|doctor|professor|prof\.?)?\s*([A-Za-z][A-Za-z'-]+(?:\s+[A-Za-z][A-Za-z'-]+)?)",
    re.IGNORECASE,
)

_ABOUT_PROF_RE = re.compile(
    r"(?:about|of)\s+(?:dr\.?|doctor|professor|prof\.?)?\s*"
    r"([A-Za-z][A-Za-z'-]+(?:\s+[A-Za-z][A-Za-z'-]+)?)",
    re.IGNORECASE,
)

# Short ALL-CAPS org abbreviations (2–6 letters).
_ORG_ABBREV_RE = re.compile(r"\b([A-Z]{2,6})\b")
# Lowercase/mixed org abbrev only when glued to an org noun (e.g. "acm organization").
_ORG_ABBREV_NEAR_NOUN_RE = re.compile(
    r"\b([A-Za-z]{2,6})\s+(?:organization|org|club|clubs|chapter|association|society)\b"
    r"|\b(?:organization|org|club|clubs|chapter|association|society)\s+([A-Za-z]{2,6})\b",
    re.IGNORECASE,
)

_STOP_ABBREV = {
    "GPA", "ACT", "SAT", "FAFSA", "FERPA", "PDF", "API", "URL", "HTTP", "HTTPS",
    "USA", "US", "AI", "IT", "HR", "VA", "ID", "OK", "AM", "PM",
    "THE", "AND", "FOR", "WITH", "FROM", "THIS", "THAT", "WHAT", "WHEN",
    "WHERE", "WHO", "HOW", "CAN", "YOU", "LET", "ME", "KNOW", "NEED", "ONLY",
    "LIST", "PLEASE", "GOING", "STATE",
}

# Words that look like faculty-name captures after "professor/dr" but are not people.
_FACULTY_NAME_STOP = {
    "means",
    "mean",
    "meaning",
    "title",
    "rank",
    "position",
    "role",
    "status",
    "level",
    "track",
    "salary",
    "pay",
    "here",
    "there",
    "this",
    "that",
    "what",
    "who",
    "when",
    "where",
    "how",
    "why",
    "assistant",
    "associate",
    "full",
    "adjunct",
    "visiting",
    "emeritus",
}

_DEFINITION_CUES = [
    r"\bwhat does\b.+\bmean\b",
    r"\bwhat is\b.+\bmean(?:s|ing)?\b",
    r"\bwhat'?s?\s+the\s+meaning\s+of\b",
    r"\bmeaning of\b",
    r"\bdefine\b",
    r"\bdefinition of\b",
    r"\bwhat does\b.+\bstand for\b",
    r"\bwhat is an?\b.+\b(?:professor|instructor|dean|advisor)\b",
]


def _has_any(q: str, patterns: list[str]) -> bool:
    return any(re.search(p, q, re.IGNORECASE) for p in patterns)


def extract_entities(question: str) -> list[DetectedEntity]:
    """Lightweight entity extraction — fails gracefully."""
    entities: list[DetectedEntity] = []
    seen: set[str] = set()

    def _add(raw: str, etype: str, aliases: list[str] | None = None) -> None:
        cleaned = _TITLE_RE.sub("", raw).strip(" .,?!'\"")
        if not cleaned or len(cleaned) < 2:
            return
        key = cleaned.lower()
        if key in seen:
            return
        # "professor means" must not invent a person named Means
        if etype == "faculty_or_staff" and (
            key in _FACULTY_NAME_STOP
            or any(part in _FACULTY_NAME_STOP for part in key.split())
        ):
            return
        seen.add(key)
        entities.append(
            DetectedEntity(
                raw_text=raw.strip(),
                normalized_name=cleaned,
                entity_type=etype,
                aliases=aliases or [],
            )
        )

    for m in _FACULTY_NAME_RE.finditer(question):
        _add(m.group(0), "faculty_or_staff")
    for m in _WHO_IS_RE.finditer(question):
        _add(m.group(1), "faculty_or_staff")
    for m in _ABOUT_PROF_RE.finditer(question):
        # Require an explicit academic title or rating cue — "tell me about X"
        # alone must not invent a faculty entity (e.g. academic programs).
        if _TITLE_RE.search(question) or _has_any(question, _RATING_CUES):
            _add(m.group(1), "faculty_or_staff")

    # Organization abbreviations (generic pattern)
    q_has_org_cues = _has_any(question, _ORG_CUES + _ACTIVITY_CUES + _SOCIAL_CUES) or (
        "organization" in question.lower()
        or "club" in question.lower()
        or "association" in question.lower()
    )
    for m in _ORG_ABBREV_RE.finditer(question):
        token = m.group(1)
        if token in _STOP_ABBREV:
            continue
        if q_has_org_cues:
            _add(token, "campus_organization")

    # "acm organization" / "organization acm" (any case)
    for m in _ORG_ABBREV_NEAR_NOUN_RE.finditer(question):
        token = (m.group(1) or m.group(2) or "").strip()
        upper = token.upper()
        if not token or upper in _STOP_ABBREV:
            continue
        _add(upper, "campus_organization")

    return entities


def classify_retrieval(question: str) -> RetrievalClassification:
    """Classify evidence needs for selective hybrid retrieval."""
    q = (question or "").strip()
    q_lower = q.lower()
    entities = extract_entities(q)

    freshness = "current" if _has_any(q_lower, _FRESHNESS_CUES) else "stable"
    secondary: list[str] = []
    companion_categories: list[str] = []
    registry_topics: list[str] = []
    confidence = 0.7

    has_faculty_entity = any(e.entity_type == "faculty_or_staff" for e in entities)
    has_org_entity = any(e.entity_type == "campus_organization" for e in entities)
    wants_ratings = _has_any(q_lower, _RATING_CUES)
    wants_social = _has_any(q_lower, _SOCIAL_CUES)
    wants_org_activity = _has_any(q_lower, _ACTIVITY_CUES) and (
        has_org_entity or _has_any(q_lower, _ORG_CUES)
    )
    wants_definition = _has_any(q_lower, _DEFINITION_CUES)

    # --- Intent priority order ---
    # Definitions before faculty identity ("what is assistant professor means?")
    if wants_definition and not wants_ratings and not wants_social:
        primary = INTENT_TERM_DEFINITION
        use_kb = True
        # KB-first; live only if user web mode escalates after KB (hybrid fast-path).
        use_official_live = False
        use_companions = False
        companion_categories = []
        registry_topics = ["faculty", "policy", "catalog"]
        reason = "Term/definition question — KB-first fast path"
        confidence = 0.88
        freshness = "stable"
        # Drop bogus person entities from rank/title phrasing
        entities = [e for e in entities if e.entity_type != "faculty_or_staff"]

    elif wants_social and (has_org_entity or _has_any(q_lower, _ORG_CUES) or wants_social):
        primary = INTENT_SOCIAL_PROFILE
        use_kb = True
        use_official_live = True
        use_companions = True
        companion_categories = ["social"]
        registry_topics = ["organization", "social"]
        reason = "Social profile discovery for a campus organization"
        if has_org_entity:
            confidence = 0.85
        freshness = "stable"

    elif wants_ratings or (has_faculty_entity and wants_ratings):
        primary = INTENT_FACULTY_RATINGS
        use_kb = True
        use_official_live = True
        use_companions = True
        companion_categories = ["student_rating"]
        registry_topics = ["faculty", "rating"]
        reason = "Faculty student-opinion / rating question"
        confidence = 0.9 if has_faculty_entity else 0.75

    elif has_faculty_entity or (
        _has_any(q_lower, _FACULTY_IDENTITY_CUES)
        and (_TITLE_RE.search(q) or _WHO_IS_RE.search(q))
    ):
        primary = INTENT_FACULTY_IDENTITY
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["faculty"]
        reason = "Faculty/staff identity — official sources only"
        confidence = 0.9 if has_faculty_entity else 0.7

    elif wants_org_activity:
        primary = INTENT_ORG_ACTIVITY
        use_kb = True
        use_official_live = True
        use_companions = True
        companion_categories = ["social"]
        registry_topics = ["organization", "events", "news"]
        freshness = "current"
        reason = "Organization activity / freshness — official live + optional social links"
        confidence = 0.85

    elif has_org_entity or _has_any(q_lower, _ORG_CUES):
        primary = INTENT_ORG_IDENTITY
        use_kb = True
        use_official_live = True
        use_companions = True
        companion_categories = ["social"]
        registry_topics = ["organization"]
        reason = "Campus organization identity"
        confidence = 0.8

    elif _has_any(q_lower, _ATHLETICS_CUES):
        primary = INTENT_ATHLETICS
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["athletics"]
        reason = "Athletics — official campus sources"
        if freshness == "stable" and _has_any(q_lower, [r"\bschedule\b", r"\bgame\b"]):
            freshness = "current"

    elif _has_any(q_lower, _ADMISSIONS_CUES):
        primary = INTENT_ADMISSIONS_POLICY
        use_kb = True
        use_official_live = freshness == "current"
        use_companions = False
        registry_topics = ["admissions", "tuition", "scholarship", "financial aid"]
        reason = "Admissions/tuition/policy — official only; no companions"

    elif _has_any(q_lower, _SERVICES_CUES):
        primary = INTENT_CAMPUS_SERVICES
        use_kb = True
        use_official_live = freshness == "current" or _has_any(q_lower, [r"\bhours?\b", r"\bcontact\b"])
        use_companions = False
        registry_topics = ["campus services"]
        reason = "Campus services — KB with live if hours/contact/current"

    elif _has_any(q_lower, _PROGRAM_CUES):
        primary = INTENT_ACADEMIC_PROGRAMS
        use_kb = True
        use_official_live = False
        use_companions = False
        registry_topics = ["programs", "catalog"]
        reason = "Academic programs — KB primary"

    elif freshness == "current" or _has_any(q_lower, [r"\bnews\b", r"\bevents?\b"]):
        primary = INTENT_EVENTS_CURRENT
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["news", "events"]
        freshness = "current"
        reason = "Current campus events/news — prefer official live"

    else:
        primary = INTENT_GENERAL
        use_kb = True
        use_official_live = False
        use_companions = False
        registry_topics = []
        reason = "General campus question — KB default"
        confidence = 0.55

    # If user asked ratings without explicit faculty entity, still allow companion
    if primary == INTENT_FACULTY_RATINGS and not has_faculty_entity:
        # Try to salvage a name from "about X" / trailing tokens
        m = re.search(
            r"(?:about|of|for)\s+([A-Za-z][A-Za-z'-]+(?:\s+[A-Za-z][A-Za-z'-]+)?)",
            q,
            re.IGNORECASE,
        )
        if m:
            entities.append(
                DetectedEntity(
                    raw_text=m.group(1),
                    normalized_name=_TITLE_RE.sub("", m.group(1)).strip(),
                    entity_type="faculty_or_staff",
                    aliases=[],
                )
            )

    # Faculty identity never activates student_rating unless ratings cues present
    if primary == INTENT_FACULTY_IDENTITY:
        use_companions = False
        companion_categories = []

    # Admissions never activates companions
    if primary == INTENT_ADMISSIONS_POLICY:
        use_companions = False
        companion_categories = []

    return RetrievalClassification(
        primary_intent=primary,
        secondary_intents=secondary,
        entities=entities,
        freshness=freshness,
        use_kb=use_kb,
        use_official_live=use_official_live,
        use_companions=use_companions,
        companion_categories=companion_categories,
        registry_topics=registry_topics,
        routing_reason=reason,
        confidence=confidence,
    )


def with_user_web_preference(
    classification: RetrievalClassification,
    use_web_search: bool,
) -> RetrievalClassification:
    """Preserve UI web-mode semantics: force official live when user selects web.

    Definition questions stay KB-first even in web mode — hybrid may escalate
    to a single official pass if KB is thin (avoids 60s+ agentic/official stacks).
    """
    if not use_web_search:
        return classification
    if classification.primary_intent == INTENT_TERM_DEFINITION:
        return replace(
            classification,
            routing_reason=classification.routing_reason
            + " | user selected web mode (definition: KB-first)",
        )
    return replace(
        classification,
        use_official_live=True,
        routing_reason=classification.routing_reason + " | user selected web mode",
    )


def looks_definitional(question: str) -> bool:
    """True for short define/meaning questions (skip heavy rewrite)."""
    return _has_any((question or "").lower(), _DEFINITION_CUES)
