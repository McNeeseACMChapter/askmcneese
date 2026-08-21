"""Deterministic retrieval classifier for RCCS.

Domain-general within AskMcNeese. Example entities (faculty names, org
abbreviations) are not hardcoded product boundaries â€” aliases come from
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
INTENT_ACADEMIC_CALENDAR = "academic_calendar"
INTENT_DEGREE_PLAN = "degree_plan"
INTENT_TERM_DEFINITION = "term_definition"
INTENT_POLICY_PROCEDURE = "policy_procedure"
INTENT_FORM_LOOKUP = "form_lookup"
INTENT_CAREER_SERVICES = "career_services"
INTENT_COURSE_CATALOG = "course_catalog"
INTENT_COURSE_SCHEDULE = "course_schedule"
INTENT_GENERAL = "general_campus"

_TITLE_RE = re.compile(
    r"\b(?:dr\.?|doctor|professor|prof\.?|dean|coach|instructor)\s+",
    re.IGNORECASE,
)

_FACULTY_IDENTITY_CUES = [
    r"\bwho is\b",
    r"\bwho was\b",
    r"\bwho were\b",
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
    r"\brequirement",
]

_ATHLETICS_CUES = [
    r"\bathletics?\b",
    r"\bsports?\b",
    r"\bcowboys?\b",
    r"\bcowgirls?\b",
    r"\bfootball\b",
    r"\bbasketball\b",
    r"\b(?:athletic|game|season)\s+tickets?\b",
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

_DEGREE_PLAN_CONTENT_CUES = [
    r"\bcourses?\b",
    r"\bclasses\b",
    r"\bcurriculum\b",
    r"\bdegree\s+plan\b",
    r"\bcourse\s+list\b",
]

_DEGREE_PLAN_COMPLETION_CUES = [
    r"\bdegree\b",
    r"\bmajor\b",
    r"\bprogram\b",
    r"\bcurriculum\b",
    r"\bgraduate\b",
    r"\bgraduation\b",
    r"\bcomplete\b",
    r"\bcompletion\b",
    r"\bfinish\b",
    r"\bwhole\b",
    r"\ball\b",
    r"\brequired\b",
    r"\brequirements\b",
]

_ACADEMIC_CALENDAR_CUES = [
    r"\bacademic\s+(?:calendar|schedule)\b",
    r"\b(?:spring|summer|fall|winter)\s+(?:semester|session|term)(?:\s+20\d{2})?\b",
    r"\b(?:spring|summer|fall|winter)\s+20\d{2}\b",
    r"\bsemester\b.*\b(?:begin|begins|start|starts|end|ends|ending|over)\b",
    r"\b(?:classes|final(?: examination| exam)?s?)\b.*\b(?:begin|begins|start|starts|end|ends|ending)\b",
    r"\b(?:add/drop|registration|withdrawal)\s+(?:date|deadline)\b",
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

# Short ALL-CAPS org abbreviations (2â€“6 letters).
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
    # Prepositions / glue words captured by "club at" / "association of" patterns
    "AT", "OF", "IN", "ON", "TO", "BY", "AN", "OR", "AS", "IF", "BE", "IS",
    "ARE", "WAS", "SO", "NO", "MY", "WE", "HE", "SHE", "NOT", "BUT", "ALL",
    "CLUB", "ORG",
}

# "Association for Computing Machinery club at McNeese"
_ORG_NAME_BEFORE_CLUB_RE = re.compile(
    r"(?i)\b(?:the\s+)?"
    r"(?!(?:what|who|where|which|how|when|is|are|was|were|tell)\b)"
    r"([A-Za-z][A-Za-z0-9&'â€™.-]+(?:\s+[A-Za-z0-9&'â€™.-]+){1,8})\s+"
    r"(?:club|organization|chapter)\s+(?:at\s+)?mcneese\b"
)
# "Nepalese Student Association at McNeese"
_ORG_ASSOCIATION_AT_RE = re.compile(
    r"(?i)\b(?:the\s+)?"
    r"([A-Za-z][A-Za-z0-9&'â€™.-]+(?:\s+[A-Za-z0-9&'â€™.-]+){0,6}\s+"
    r"(?:Student\s+)?(?:Association|Society))\s+at\s+mcneese\b"
)

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
    "of",
    "the",
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


_FORM_CUES = [
    r"\bforms?\b", r"\bdownload\b", r"\bfill(?:ing)?\s+(?:out\s+)?(?:a|the)\b",
    r"\bwhere\b.+\b(?:submit|file|request|application)\b",
    r"\bhow\b.+\b(?:submit|file|request|appeal|apply)\b",
]

_POLICY_PROCEDURE_CUES = [
    r"\bpolic(?:y|ies)\b", r"\bappeal\b", r"\bsuspension\b", r"\bprobation\b",
    r"\bwithdraw(?:al)?\b", r"\bdrop\b.+\bcourses?\b", r"\bcomplaint\b",
    r"\breport\b.+\b(?:misconduct|harassment|assault|discrimination)\b",
    r"\bferpa\b", r"\bgrade\s+appeal\b", r"\bacademic\s+integrity\b",
]

_CAREER_CUES = [
    r"\bhandshake\b", r"\binternships?\b", r"\bco-?ops?\b", r"\bcareer\s+center\b",
    r"\bstudent\s+(?:jobs?|employment)\b", r"\bon-campus\s+(?:jobs?|employment)\b",
    r"\bresume\b", r"\bjob\s+(?:search|posting|application)\b",
]

_COURSE_CODE_RE = re.compile(
    r"\b(?!fall|spring|summer|winter|man|many|much|more|most|some|each|"
    r"take|need|earn|only|least|about|over|under|from|with|into|"
    r"than|level|class|course|hours?|credits?)[A-Z]{2,5}\s*\d{3,4}[A-Z]?\b",
    re.IGNORECASE,
)
_UPPER_DIVISION_REQ_RE = re.compile(
    r"\b(?:300\s*/\s*400|400[- ]?level|300[- ]?level|upper[- ]division)\b",
    re.IGNORECASE,
)

def _has_any(q: str, patterns: list[str]) -> bool:
    return any(re.search(p, q, re.IGNORECASE) for p in patterns)


def extract_entities(question: str) -> list[DetectedEntity]:
    """Lightweight entity extraction â€” fails gracefully."""
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
        # Require an explicit academic title or rating cue â€” "tell me about X"
        # alone must not invent a faculty entity (e.g. academic programs).
        if (_TITLE_RE.search(question) and not re.search(r"\b(?:dean|chair|head|director)\s+of\b", question, re.I)) or _has_any(question, _RATING_CUES):
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

    # Full org names: "â€¦ club at McNeese" / "â€¦ Association at McNeese"
    for pattern in (_ORG_NAME_BEFORE_CLUB_RE, _ORG_ASSOCIATION_AT_RE):
        for m in pattern.finditer(question):
            name = (m.group(1) or "").strip(" .,?!'\"")
            name = re.sub(
                r"^(?:what is|what'?s|who is|tell me about|is|are)\s+(?:the\s+)?",
                "",
                name,
                flags=re.IGNORECASE,
            ).strip()
            if name and len(name) > 3 and name.lower() not in {"the club", "a club"}:
                _add(name, "campus_organization")

    return entities


def classify_retrieval(question: str, *, campus_query=None) -> RetrievalClassification:
    """Classify evidence needs for selective hybrid retrieval."""
    q = (question or "").strip()
    q_lower = q.lower()
    entities = extract_entities(q)
    compiled_query: dict = {}
    compiled_domain = ""
    compiled_freshness = ""
    try:
        from app.services.campus_intelligence.compiler import compile_campus_query

        compiled = campus_query or compile_campus_query(q)
        compiled_query = compiled.to_dict()
        compiled_domain = compiled.domain
        compiled_freshness = compiled.freshness
    except Exception:
        # The versioned compiler is additive; a configuration failure keeps the
        # legacy classifier available as the rollback path.
        pass

    freshness = "current" if (
        compiled_freshness in {"live", "term_based"} or _has_any(q_lower, _FRESHNESS_CUES)
    ) else "stable"
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
    wants_form = _has_any(q_lower, _FORM_CUES)
    wants_policy = _has_any(q_lower, _POLICY_PROCEDURE_CUES) or compiled_domain == "policy"
    wants_career = _has_any(q_lower, _CAREER_CUES) or compiled_domain == "employment"
    wants_course_catalog = compiled_domain == "catalog" or bool(_COURSE_CODE_RE.search(q)) or bool(
        re.search(r"\b(?:course|class)\s+(?:description|prerequisite|credit hours?)\b", q_lower)
    )
    wants_course_schedule = bool(
        (compiled_query or {}).get("answer_shape") in {
            "schedule_conflict_result",
            "course_offering_result",
        }
        or (
            re.search(r"\b(?:conflict(?:s|ing)?|overlap(?:s|ping|ped)?)\b", q_lower)
            and re.search(r"\b(?:courses?|classes?|sections?)\b", q_lower)
        )
    )
    if wants_course_schedule:
        wants_course_catalog = False
    wants_form = wants_form and not (wants_career or wants_course_catalog or compiled_domain == "admissions")
    wants_definition = _has_any(q_lower, _DEFINITION_CUES) and not (
        wants_form or wants_policy or wants_career or wants_course_catalog
    )
    course_inventory_request = bool(
        re.search(r"\b(?:courses?|classes?|sections?|crns?)\b", q_lower)
        and re.search(
            r"\b(?:show|find|list|offered|offering|available|sections?|crns?|class\s+planner)\b",
            q_lower,
        )
        and not re.search(
            r"\b(?:deadline|last\s+(?:day|date)|withdraw(?:al|ing)?|add\s*/?\s*drop|"
            r"classes?\s+(?:begin|start|end))\b",
            q_lower,
        )
    )
    wants_academic_calendar = (
        (compiled_domain == "academic_calendar" or _has_any(q_lower, _ACADEMIC_CALENDAR_CUES))
        and not _has_any(q_lower, _ATHLETICS_CUES)
        and not course_inventory_request
    )
    wants_upper_division_req = bool(_UPPER_DIVISION_REQ_RE.search(q)) and (
        _has_any(q_lower, _PROGRAM_CUES)
        or _has_any(q_lower, _DEGREE_PLAN_COMPLETION_CUES)
        or _has_any(q_lower, [r"\bhours?\b", r"\bcredits?\b", r"\bearn\b", r"\bneed\b"])
    )
    wants_degree_plan = (
        compiled_domain == "degree_requirements"
        or wants_upper_division_req
        or (
            _has_any(q_lower, _DEGREE_PLAN_CONTENT_CUES)
            and _has_any(q_lower, _DEGREE_PLAN_COMPLETION_CUES)
            and _has_any(q_lower, _PROGRAM_CUES)
            and not _has_any(q_lower, [r"\bwithdraw", r"\bdrop\b", r"\badd\b"])
        )
    )
    # Upper-division hour rules live on degree plans, not course-description pages.
    if wants_upper_division_req or (
        wants_degree_plan and not bool(_COURSE_CODE_RE.search(q))
        and not re.search(
            r"\b(?:course|class)\s+(?:description|prerequisite)\b",
            q_lower,
        )
    ):
        wants_course_catalog = False
    # Inventory/count/list of majors must not enter the named degree-plan specialist.
    try:
        from app.services.program_inventory import is_program_inventory_question

        wants_program_inventory = is_program_inventory_question(q)
    except Exception:
        wants_program_inventory = False
    if wants_program_inventory:
        wants_degree_plan = False

    # --- Intent priority order ---
    # Actionable campus procedures must beat loose definition/admission/athletics cues.
    if wants_course_schedule:
        primary = INTENT_COURSE_SCHEDULE
        use_kb = False
        use_official_live = False
        use_companions = False
        registry_topics = ["class planner", "course schedule", "meeting conflicts"]
        freshness = "current"
        reason = "Course schedule conflict — structured Class Planner execution required"
        confidence = 0.98

    elif wants_form:
        primary = INTENT_FORM_LOOKUP
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["forms", "applications", "requests", "appeals"]
        reason = "Form/action lookup â€” exact official destination required"
        confidence = 0.94

    elif wants_policy:
        primary = INTENT_POLICY_PROCEDURE
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["policy", "procedure", "appeals", "student handbook"]
        reason = "Policy/procedure question â€” official rule and action path required"
        confidence = 0.93

    elif wants_career:
        primary = INTENT_CAREER_SERVICES
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["career", "Handshake", "jobs", "internships", "co-op"]
        reason = "Career-services question â€” official service and platform path required"
        confidence = 0.94

    elif wants_degree_plan and wants_upper_division_req:
        primary = INTENT_DEGREE_PLAN
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["academic catalog", "curriculum", "degree requirements"]
        freshness = "current"
        reason = "Upper-division 300/400-level requirement — current degree plan"
        confidence = 0.96

    elif wants_course_catalog:
        primary = INTENT_COURSE_CATALOG
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["course catalog", "course descriptions", "prerequisites"]
        freshness = "current"
        reason = "Specific course lookup â€” current catalog evidence required"
        confidence = 0.95

    # Definitions before faculty identity ("what is assistant professor means?")
    elif wants_definition and not wants_ratings and not wants_social:
        primary = INTENT_TERM_DEFINITION
        use_kb = True
        # KB-first; live only if user web mode escalates after KB (hybrid fast-path).
        use_official_live = False
        use_companions = False
        companion_categories = []
        registry_topics = ["faculty", "policy", "catalog"]
        reason = "Term/definition question â€” KB-first fast path"
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
        reason = "Faculty/staff identity â€” official sources only"
        confidence = 0.9 if has_faculty_entity else 0.7

    elif wants_org_activity:
        primary = INTENT_ORG_ACTIVITY
        use_kb = True
        use_official_live = True
        use_companions = True
        companion_categories = ["social"]
        registry_topics = ["organization", "events", "news"]
        freshness = "current"
        reason = "Organization activity / freshness â€” official live + optional social links"
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

    elif wants_academic_calendar:
        primary = INTENT_ACADEMIC_CALENDAR
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["academic schedule", "academic calendar", "semester dates"]
        freshness = "current"
        reason = "Academic calendar/date question â€” direct official schedule page"
        confidence = 0.94

    elif wants_program_inventory:
        primary = INTENT_ACADEMIC_PROGRAMS
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["undergraduate programs", "majors", "programs", "catalog"]
        freshness = "current"
        reason = "Undergraduate majors inventory — count titles from official programs directory"
        confidence = 0.96

    elif wants_degree_plan:
        primary = INTENT_DEGREE_PLAN
        use_kb = False
        use_official_live = True
        use_companions = False
        registry_topics = ["academic catalog", "curriculum", "degree requirements"]
        freshness = "current"
        reason = "Named degree-plan question â€” current official catalog curriculum"
        confidence = 0.94

    elif _has_any(q_lower, _ATHLETICS_CUES):
        primary = INTENT_ATHLETICS
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["athletics"]
        reason = "Athletics â€” official campus sources"
        if freshness == "stable" and _has_any(q_lower, [r"\bschedule\b", r"\bgame\b"]):
            freshness = "current"
        # Schedules/tickets live on mcneesesports.com; KB has almost no athletics pages
        # and expansion used to poison these with admissions neighbors.
        if _has_any(
            q_lower,
            [r"\bschedule\b", r"\bgames?\b", r"\btickets?\b", r"\bnext\b", r"\bwhen\b", r"\broster\b"],
        ):
            use_kb = False
            freshness = "current"
            reason = "Athletics schedule/tickets â€” official live (mcneesesports.com)"

    elif compiled_domain in {"admissions", "financial_aid", "student_finance"} or _has_any(q_lower, _ADMISSIONS_CUES):
        primary = INTENT_ADMISSIONS_POLICY
        use_kb = True
        use_official_live = freshness == "current"
        use_companions = False
        registry_topics = ["admissions", "tuition", "scholarship", "financial aid"]
        reason = "Admissions/tuition/policy â€” official only; no companions"

    elif compiled_domain in {"student_services", "wellbeing", "international_services", "technology", "locations", "academic_support", "directory", "records", "registration", "safety"} or _has_any(q_lower, _SERVICES_CUES):
        primary = INTENT_CAMPUS_SERVICES
        use_kb = True
        use_official_live = freshness == "current" or _has_any(q_lower, [r"\bhours?\b", r"\bcontact\b"])
        use_companions = False
        registry_topics = ["campus services"]
        reason = "Campus services â€” KB with live if hours/contact/current"

    elif _has_any(q_lower, _PROGRAM_CUES):
        primary = INTENT_ACADEMIC_PROGRAMS
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["programs", "catalog"]
        reason = "Academic programs â€” KB plus current official catalog"

    elif freshness == "current" or _has_any(q_lower, [r"\bnews\b", r"\bevents?\b"]):
        primary = INTENT_EVENTS_CURRENT
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["news", "events"]
        freshness = "current"
        reason = "Current campus events/news â€” prefer official live"

    else:
        primary = INTENT_GENERAL
        use_kb = True
        use_official_live = True
        use_companions = False
        registry_topics = ["mcneese"]
        reason = "General campus question â€” KB plus official discovery fallback"
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

    # Enrich topics from the whole source registry match (not hand-coded intents alone).
    try:
        from app.services.source_registry import match_registry

        reg = match_registry(question, max_sources=4)
        for topic in reg.topics:
            if topic and topic not in registry_topics:
                registry_topics.append(topic)
        # If registry strongly matched an external live hub, prefer official live.
        top_id = reg.source_ids[0] if reg.source_ids else ""
        top_score = reg.scores.get(top_id, 0)
        if top_score >= 6 and top_id in {"SRC-028", "SRC-035", "SRC-036", "SRC-029"}:
            use_official_live = True
            if top_id == "SRC-028" and _has_any(
                q_lower,
                [r"\bschedule\b", r"\bgames?\b", r"\btickets?\b", r"\bnext\b", r"\bwhen\b", r"\broster\b"],
            ):
                use_kb = False
                freshness = "current"
                if primary == INTENT_GENERAL:
                    primary = INTENT_ATHLETICS
                    reason = "Registry match â†’ athletics live sources"
    except Exception:
        pass

    if compiled_query:
        reason = f"campus_query={compiled_query.get('domain')}/{compiled_query.get('intent')} | {reason}"
        confidence = max(confidence, float(compiled_query.get("confidence") or 0.0))

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
        compiled_query=compiled_query,
    )


def with_user_web_preference(
    classification: RetrievalClassification,
    use_web_search: bool,
) -> RetrievalClassification:
    """Preserve UI web-mode semantics: force official live when user selects web.

    Definition questions stay KB-first even in web mode â€” hybrid may escalate
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


_SOCIAL_LINK_LOOKUP = [
    r"\b(?:facebook|instagram|linkedin|twitter|youtube|tiktok)\s+page\b",
    r"\b(?:facebook|instagram|linkedin|twitter|youtube)\s+profile\b",
    r"\b(?:facebook|instagram|linkedin)\s+(?:link|url|account)\b",
    r"\bwhat is (?:the )?(?:facebook|instagram|linkedin|twitter|youtube)\b",
    r"\b(?:official )?(?:facebook|instagram|linkedin|twitter|youtube) (?:for|of)\b",
    r"\bwhere (?:can i find|is) (?:the )?(?:facebook|instagram|linkedin|twitter|youtube)\b",
]

_SOCIAL_CONTENT_CUES = [
    r"\bposts?\b",
    r"\brecent(?:ly)?\b",
    r"\blatest\b",
    r"\bhappening\b",
    r"\bactivity\b",
    r"\bfollowers?\b",
    r"\bwhat(?:'s| is) going on\b",
    r"\bannouncements?\b",
]


def looks_social_link_lookup(question: str) -> bool:
    """True when the user mainly wants a social/profile URL, not live posts."""
    q = (question or "").lower()
    if not _has_any(q, _SOCIAL_LINK_LOOKUP) and not (
        _has_any(q, _SOCIAL_CUES) and re.search(r"\b(?:page|profile|link|url|account)\b", q)
    ):
        return False
    # Content/activity asks need crawl â€” not the link-only fast path.
    if _has_any(q, _SOCIAL_CONTENT_CUES):
        return False
    return True


def wants_social_page_content(question: str) -> bool:
    """True when the user asked for posts/activity from a social/org page."""
    q = (question or "").lower()
    return _has_any(q, _SOCIAL_CUES) and _has_any(q, _SOCIAL_CONTENT_CUES)


