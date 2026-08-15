"""Compile natural language into a domain-general campus operation.

The high-confidence path is deterministic and configuration-driven. This keeps
capability discovery, common paraphrases, misspellings, freshness, risk, source
groups, and answer shapes out of the LLM routing loop.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import replace
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.services.academic_calendar import resolve_academic_term

from .full_spectrum import (
    answer_shape_for_schema,
    build_full_spectrum_plan,
    clear_full_spectrum_caches,
    requires_live_discovery,
)
from .models import CampusQuery
from .registry import get_domain_pack, load_domain_pack_registry


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
_GENERIC = {
    "mcneese", "university", "state", "school", "campus", "question", "questions",
    "please", "tell", "give", "need", "want", "help", "about", "with", "what",
    "where", "when", "which", "who", "how", "can", "could", "would", "does",
    "the", "and", "for", "from", "into", "there", "any", "available", "a", "an",
    "are", "at", "by", "do", "i", "in", "is", "it", "me", "my", "of", "on", "to", "you", "your",
}

_INTENT_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("capability_discovery", (
        r"\bwhat (?:can|could) you (?:answer|do|help with)\b",
        r"\bwhat (?:kinds?|types?) of .*questions\b",
        r"\bshow (?:me )?(?:your )?capabilit",
        r"\bwhat can i ask\b",
        r"\bhow can you help\b",
        r"\bwhat topics? do you know\b",
        r"\bcan you (?:do|use) (?:a |the )?(?:web |internet )?(?:search|browsing)\b",
        r"\bcan you (?:search|browse|look up) (?:the )?(?:web|internet)\b",
        r"\bdo you have (?:internet|web|browsing) access\b",
        r"\bare you able to (?:answer|help|search|browse)\b",
    )),
    ("source_trust_explanation", (r"\bwhat sources?\b", r"\bwhy (?:should|can) i trust\b", r"\bsource trust\b")),
    ("help_examples", (r"\bexamples? of (?:questions|things)\b", r"\bhelp examples?\b")),
    ("find_form", (r"\bforms?\b", r"\bdownload\b", r"\bwhere .*\b(?:submit|file)\b")),
    ("find_contact", (r"\bwho (?:do|should|can) i contact\b", r"\bcontact (?:for|about)\b", r"\bphone(?: number)?\b", r"\bemail(?: address)?\b", r"\bwho handles\b")),
    ("check_deadline", (r"\bdeadline\b", r"\bwhen (?:does|do|is|are|can)\b", r"\bwhat date\b", r"\bstarts?\b", r"\bends?|ending\b")),
    ("check_status", (r"\bmy .*status\b", r"\bstatus of my\b", r"\bcheck my\b")),
    ("check_eligibility", (r"\bam i eligible\b", r"\bcan i qualify\b", r"\beligib")),
    ("check_availability", (r"\b(?:is|are) there\b", r"\bavailab", r"\bopen(?:ings?)?\b", r"\bactive\b")),
    ("apply", (r"\bhow (?:do|can) i apply\b", r"\bapply (?:to|for|now)\b", r"\bapplication link\b", r"\bwhere .*\bapply\b")),
    ("register", (r"\bregister(?: for)?\b", r"\benroll in (?:a )?class\b")),
    ("pay", (r"\bpay (?:my )?(?:tuition|bill|fees?)\b", r"\bpayment portal\b")),
    ("calculate", (r"\bhow much (?:will|would|do)\b", r"\bcalculate\b", r"\bestimate (?:my )?cost\b")),
    ("appeal", (r"\bappeal\b",)),
    ("resolve_problem", (r"\breset\b", r"\bnot working\b", r"\blocked\b", r"\bproblem\b", r"\bcan't\b", r"\bcannot\b")),
    ("find_process", (r"\bhow (?:do|can) i\b", r"\bwhat is the process\b", r"\bwhat steps\b")),
    ("find_policy", (r"\bpolic(?:y|ies)\b", r"\brules? (?:for|about)\b")),
    ("find_job", (r"\bjobs?\b", r"\bpositions?\b", r"\bemployment opportunities\b", r"\bhiring\b")),
    (
        "find_course",
        (
            # Avoid seasons, English quantifiers, and "400 level" phrasing as
            # fake course codes (e.g. "how many 400 level courses").
            r"\b(?!fall|spring|summer|winter|man|many|much|more|most|some|each|"
            r"take|need|earn|only|least|about|over|under|from|with|into|"
            r"than|level|class|course|hours?|credits?)[A-Za-z]{2,5}\s*\d{3,4}[A-Za-z]?\b",
            r"\bcourse description\b",
            r"\bfind .*courses?\b",
        ),
    ),
    ("find_event", (r"\bevents?\b", r"\bwhat(?:'s| is) happening\b", r"\bwhat(?:'s| is) going on\b")),
    ("find_organization", (r"\bfind .*\b(?:club|organization|association)\b", r"\bwhat is .*\b(?:club|organization)\b")),
    (
        "identify_person",
        (
            r"\bwho is\b",
            r"\bwho teaches\b",
            r"\bprofessor\b",
            r"\bwho (?:is|was|were) (?:the )?(?:dean|chair|head|director)\b",
        ),
    ),
    ("identify_office", (r"\bwhich office\b", r"\bwhat office\b")),
    ("locate", (r"\bwhere is\b", r"\blocat(?:e|ion)\b", r"\bdirections?\b", r"\bmap\b")),
    ("compare", (r"\bcompare\b", r"\bdifference between\b", r"\bversus\b", r"\bvs\.?\b")),
    ("check_requirements", (r"\brequirements?\b", r"\bwhat (?:classes|courses|documents) (?:are|do i) need\b", r"\bwhat documents do .* need\b", r"\bdocuments .* required\b", r"\bclasses .*required\b", r"\bcourses .*required\b", r"\bcomplete (?:the|my) .*degree\b")),
    ("discover", (r"\bwhat .* (?:available|offer)\b", r"\bshow me\b", r"\bwhat .* (?:clubs|programs|majors)\b")),
    ("list", (r"\blist\b", r"\bwhat are (?:all|the)\b")),
    ("navigate", (
        r"\bwhere (?:do|can|should) i (?:go|log in|login)\b",
        r"\bwhere (?:do|can|should) i (?:buy|purchase|order|get|find)\b",
        r"\b(?:buy|purchase|order) (?:a |an |the |this |that )?\w+",
        r"\bportal\b", r"\blink\b",
    )),
    ("explain", (r"\bwhat is\b", r"\bexplain\b", r"\btell me about\b", r"\bhow does\b")),
]


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("â€™", "'").replace("â€˜", "'").replace("â€œ", '"').replace("â€", '"')
    text = re.sub(r"\bautumn\b", "fall", text, flags=re.I)
    text = re.sub(r"\btimetable\b", "schedule", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip().lower()


def _stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def _tokens(text: str) -> set[str]:
    return {
        _stem(token)
        for token in _TOKEN_RE.findall(text)
        if len(token) > 1 and token not in _GENERIC
    }


@lru_cache(maxsize=1)
def _misspellings() -> dict[str, str]:
    out: dict[str, str] = {}
    for pack in load_domain_pack_registry()["packs"].values():
        out.update({str(k).lower(): str(v).lower() for k, v in (pack.get("common_misspellings") or {}).items()})
    return out


def _apply_known_misspellings(text: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    result = text
    for wrong, right in _misspellings().items():
        replaced = re.sub(rf"\b{re.escape(wrong)}\b", right, result)
        if replaced != result:
            reasons.append(f"normalized known misspelling {wrong!r} to {right!r}")
            result = replaced
    return result, reasons


def _domain_scores(query: str) -> list[tuple[float, str, str]]:
    q_tokens = _tokens(query)
    scored: list[tuple[float, str, str]] = []
    for domain_id, pack in load_domain_pack_registry()["packs"].items():
        # Product self-knowledge is an explicit utterance intent, never a fuzzy
        # topical domain. Pronoun overlap previously let ordinary requests such
        # as "Where can I buy..." hijack the capability route.
        if domain_id == "capability_discovery":
            continue
        best = 0.0
        matched = ""
        for phrase in pack.get("synonyms") or []:
            normalized = _normalize(phrase)
            p_tokens = _tokens(normalized)
            if not p_tokens:
                continue
            if re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", query):
                score = 8.0 + min(len(p_tokens), 4) * 1.5
            else:
                overlap = len(q_tokens & p_tokens)
                coverage = overlap / max(len(p_tokens), 1)
                query_coverage = overlap / max(len(q_tokens), 1)
                score = overlap * 2.2 + coverage * 2.5 + query_coverage
                if overlap and SequenceMatcher(None, normalized, query).ratio() >= 0.72:
                    score += 1.0
            if score > best:
                best, matched = score, phrase
        if best:
            scored.append((best, domain_id, matched))
    scored.sort(reverse=True)
    return scored


def _detect_intent(q: str, domain: str) -> tuple[str, str | None, str]:
    for intent, patterns in _INTENT_PATTERNS:
        if any(re.search(pattern, q, re.IGNORECASE) for pattern in patterns):
            action = {
                "apply": "apply", "register": "register", "pay": "pay",
                "find_form": "download", "navigate": "navigate", "appeal": "appeal",
                "find_contact": "contact", "locate": "locate", "calculate": "calculate",
            }.get(intent)
            return intent, action, f"intent pattern matched {intent}"
    pack = get_domain_pack(domain) or {}
    supported = pack.get("supported_intents") or ["explain"]
    default = "discover" if "discover" in supported else ("explain" if "explain" in supported else supported[0])
    return default, None, f"used domain-pack default intent {default}"


def _supported_intent(domain: str, detected: str, q: str) -> str:
    pack = get_domain_pack(domain) or {}
    supported = list(pack.get("supported_intents") or [])
    if detected in supported:
        return detected
    aliases = {
        "find_job": ["discover", "check_availability"],
        "find_policy": ["explain", "find_process"],
        "find_process": ["apply", "explain", "resolve_problem"],
        "check_requirements": ["find_requirements", "explain"],
        "discover": ["list", "search", "explain"],
        "list": ["discover", "search", "explain"],
        "navigate": ["check_availability", "apply", "find_form", "explain"],
        "locate": ["find_contact", "navigate", "explain"],
        "appeal": ["find_process", "find_form", "explain"],
        "find_event": ["discover", "find_current_information"],
        "find_organization": ["discover", "search"],
        "identify_person": ["find_contact", "search"],
        "identify_office": ["find_contact", "search"],
    }
    for candidate in aliases.get(detected, []):
        if candidate in supported:
            return candidate
    return supported[0] if supported else detected


def _audience(q: str) -> tuple[str, str | None]:
    patterns = [
        ("prospective_international_undergraduate", r"\binternational\s+undergraduate\s+(?:student|applicant)\b|\bundergraduate\s+(?:international\s+)?applicant\b"),
        ("prospective_international_student", r"\binternational (?:student|applicant)|\bforeign student\b"),
        ("transfer_student", r"\btransfer (?:student|applicant)|\btransfer to mcneese\b"),
        ("graduate_applicant", r"\bgraduate (?:applicant|admission|school|program)|\bmaster'?s\b|\bdoctoral\b"),
        ("prospective_undergraduate", r"\bfreshm(?:an|en)|\bfirst[- ]time student\b|\bundergraduate applicant\b"),
        ("international_student", r"\bvisa\b|\bi-20\b|\bsevis\b|\bf-1\b"),
        ("graduate_student", r"\bgraduate assistant(?:ship)?\b|\bgrad student\b"),
        ("current_student", r"\bcurrent student\b|\bmy (?:classes|degree|account|bill|transcript|status)\b|\bon campus\b"),
        ("faculty", r"\bi am (?:a )?faculty\b|\bfaculty member\b"),
        ("staff", r"\bi am (?:a )?staff\b|\bstaff member\b"),
        ("alumni", r"\balumn(?:us|a|i|ae)\b"),
        ("parent_or_family", r"\bparent\b|\bfamily member\b"),
        ("visitor", r"\bvisitor\b|\bvisit campus\b"),
    ]
    for audience, pattern in patterns:
        if re.search(pattern, q):
            return audience, f"audience cue matched {audience}"
    return "unknown", None


def _subdomain(domain: str, q: str) -> str | None:
    rules = {
        "admissions": [("international", r"\binternational|\bvisa\b"), ("transfer", r"\btransfer\b"), ("graduate", r"\bgraduate\b|\bmaster'?s\b|\bdoctoral\b"), ("undergraduate", r"\bfreshm|\bundergraduate\b|\bfirst[- ]time\b"), ("application", r"\bapply|\bapplication\b")],
        "employment": [("student_employment", r"\bstudent jobs?|\bjobs? (?:available )?(?:to|for) students?\b|\bon[- ]campus (?:jobs?|work|employment)\b"), ("graduate_assistantships", r"\bgraduate assistant"), ("career_handshake", r"\bhandshake\b|\binternship\b|\bco-?op\b|\bcareer"), ("faculty_staff_positions", r"\bfaculty|\bstaff|\buniversity jobs?|\bwork at mcneese\b")],
        "policy": [("suspension_appeal", r"\bsuspension\b.*\bappeal\b|\bappeal\b.*\bsuspension\b"), ("academic_standing", r"\bsuspension\b|\bprobation\b|\bacademic standing\b"), ("title_ix", r"\btitle ix\b|\btitle 9\b")],
        "forms": [("suspension_appeal", r"\bsuspension\b.*\bappeal\b|\bappeal\b.*\bsuspension\b"), ("registrar", r"\bmajor change\b|\bname change\b|\baddress change\b|\btranscript\b"), ("financial_aid", r"\bfinancial aid\b|\bfafsa\b")],
        "student_services": [("housing", r"\bhousing\b|\bdorm\b|\bresidence"), ("dining", r"\bdining\b|\bmeal plan\b"), ("bookstore", r"\bbookstore\b|\btextbook|\bbook\b|\bnovel\b")],
        "wellbeing": [("counseling", r"\bcounsel|\bmental health\b"), ("accessibility", r"\baccessib|\baccommodation|\bdisability"), ("health", r"\bhealth\b|\bclinic\b|\bmedical\b|\bsick\b|\bnurse\b")],
        "technology": [("accounts_passwords", r"\bpassword\b|\baccount locked\b"), ("canvas", r"\bcanvas\b"), ("support", r"\btechnology|\bit help|\bwifi\b")],
        "locations": [("parking", r"\bparking\b"), ("maps", r"\bmap\b|\bdirections\b"), ("campus_location", r"\bwhere is\b|\blocation\b")],
        "registration": [("student_id", r"\b(?:student|mcneese) id card\b|\bid card\b|\bcowboy card\b")],
    }
    for subdomain, pattern in rules.get(domain, []):
        if re.search(pattern, q):
            return subdomain
    return None


def _entities(q: str, domain: str, subdomain: str | None) -> dict[str, Any]:
    entities: dict[str, Any] = {
        "program": None, "course": None, "office": None, "person": None,
        "term": None, "form": None, "policy": None, "location": None, "item": None,
        "subject": None, "constraint_course": None, "constraint_section": None,
    }
    term = resolve_academic_term(q)
    if term is not None:
        entities["term"] = term.label.lower()
    course = re.search(r"\b([a-z]{2,5})\s*(\d{3,4}[a-z]?)\b", q, re.IGNORECASE)
    if course and course.group(1).lower() not in {"fall", "spring", "summer", "winter"}:
        entities["course"] = f"{course.group(1).upper()} {course.group(2).upper()}"
    programs = ["mechanical engineering", "computer science", "nursing", "engineering", "biology", "business", "psychology"]
    entities["program"] = next((p for p in programs if p in q), None)
    office = re.search(r"\b(?:contact|office|department)(?: for| about| of)?\s+([a-z][a-z &-]{2,60})", q)
    if office:
        entities["office"] = office.group(1).strip(" ?.!")
    if domain == "forms" or " form" in q:
        match = re.search(r"\b(?:the |an? )?([a-z][a-z -]{2,70}?)\s+form\b", q)
        entities["form"] = (match.group(1).strip() if match else subdomain)
    if domain == "policy" or any(word in q for word in ("policy", "suspension", "probation", "appeal")):
        if "suspension" in q:
            entities["policy"] = "academic suspension"
        elif "probation" in q:
            entities["policy"] = "academic probation"
    if domain == "directory":
        person = re.search(
            r"\bwho is\s+(?:the\s+)?(?:(?:dr|doctor|professor|prof)\.?\s+)?"
            r"([a-z][a-z'-]+(?:\s+[a-z][a-z'-]+){0,3}?)"
            r"(?:\s+at\s+mcneese)?[?.!]*$",
            q,
        )
        if person:
            entities["person"] = person.group(1).strip()
        leadership = re.search(
            r"\bwho (?:is|was|were) (?:the )?"
            r"(dean|chair|head|director)(?:\s+of)?\s+(?:the\s+)?"
            r"([a-z0-9 &'-]{2,80})",
            q,
        )
        if leadership:
            entities["office"] = leadership.group(2).strip(" ?.!/")
    location = re.search(r"\bwhere is\s+([a-z][a-z0-9 &'-]{2,60})", q)
    if location:
        entities["location"] = location.group(1).strip(" ?.!")
    if domain == "student_services" and subdomain == "bookstore":
        purchase = re.search(
            r"\b(?:buy|purchase|order|get|find)\s+(.+?)[?.!]*$",
            q,
        )
        if purchase:
            item = re.sub(r"^(?:a copy of|copy of|an|a|the)\s+", "", purchase.group(1)).strip()
            item = re.sub(r"\s+(?:book|novel|textbook)$", "", item).strip()
            if item:
                entities["item"] = item
    if re.search(r"\bconflict(?:s|ing)?\b|\boverlap(?:s|ping|ped)?\b", q):
        # A follow-up can begin with "this Calculus II course" before the
        # carried schedule anchor. Do not mistake the Roman numeral/pronoun for
        # the department; keep the real subject from the original task.
        subject_stopwords = {"all", "any", "ii", "iii", "iv", "same", "that", "these", "this"}
        for subject in re.finditer(
            r"\b(?:all\s+)?([a-z]{2,5})\s+(?:courses?|classes?|sections?)\b",
            q,
        ):
            candidate = subject.group(1).lower()
            if candidate not in subject_stopwords:
                entities["subject"] = candidate.upper()
                break
        if not entities["subject"] and entities.get("program"):
            entities["subject"] = entities["program"]
        explicit_constraint = re.search(
            r"(?:selected\s+)?(?:calculus\s+ii\s+)?constraint\s+crn\s+(\d{5})",
            q,
            re.I,
        )
        crns = re.findall(r"(?<!\d)(\d{5})(?!\d)", q)
        if explicit_constraint:
            entities["constraint_section"] = explicit_constraint.group(1)
        if crns:
            entities["constraint_section"] = entities["constraint_section"] or crns[0]
        constraint = re.search(
            r"\b(?:do not|don't|does not|doesn't|without)\s+conflict(?:ing)?\s+with\s+"
            r"([^?.!]+?)(?:\s+(?:section|crn)\s+([a-z0-9-]+))?(?:[?.!]|$)",
            q,
        )
        if constraint:
            title = re.split(r"[?)!]|\s*\(continuing\s+from:", constraint.group(1), maxsplit=1, flags=re.I)[0].strip(" .")
            title = re.sub(r"\bii\b", "II", title.title(), flags=re.I)
            entities["constraint_course"] = title
            entities["constraint_section"] = entities["constraint_section"] or constraint.group(2)
        overlap_constraint = re.search(
            r"\b(?:not|never|without|won't|will not|do not|does not)\s+overlap(?:ping)?\s+"
            r"(?:with\s+)?([a-z]{2,5}\s*\d{3,4}[a-z]?)",
            q,
            re.I,
        )
        if overlap_constraint:
            entities["constraint_course"] = re.sub(
                r"\s+", " ", overlap_constraint.group(1).upper()
            )
        elif not entities["constraint_course"] and entities.get("course"):
            entities["constraint_course"] = entities["course"]
    return entities


def _source_groups(domain: str, subdomain: str | None, intent: str, pack: dict[str, Any]) -> list[str]:
    groups = list(pack.get("source_groups") or [])
    preferred: list[str] = []
    mapping = {
        ("admissions", "international"): ["international_admissions", "official_admissions", "application_portal"],
        ("admissions", "transfer"): ["transfer_admissions", "official_admissions", "application_portal"],
        ("admissions", "graduate"): ["graduate_admissions", "official_admissions", "application_portal"],
        ("employment", "student_employment"): ["student_employment", "official_employment"],
        ("employment", "graduate_assistantships"): ["graduate_assistantships", "official_employment"],
        ("employment", "career_handshake"): ["career_center", "official_employment"],
        ("employment", "faculty_staff_positions"): ["official_employment", "employment_portals"],
        ("policy", "suspension_appeal"): ["academic_standing", "official_policies", "official_forms"],
        ("policy", "academic_standing"): ["academic_standing", "official_policies"],
        ("student_services", "housing"): ["housing"],
        ("student_services", "dining"): ["dining"],
        ("student_services", "bookstore"): ["bookstore"],
        ("wellbeing", "counseling"): ["counseling"],
        ("wellbeing", "accessibility"): ["accessibility"],
        ("wellbeing", "health"): ["health_services"],
        ("locations", "parking"): ["parking_transportation"],
        ("registration", "student_id"): ["registration"],
    }
    scoped = list(mapping.get((domain, subdomain), []))
    if scoped:
        # A resolved subdomain owns its retrieval lane. Do not fan a bookstore
        # question into housing/dining, or a student-job query into every job feed.
        return list(dict.fromkeys(scoped))
    if domain == "admissions" and intent in {"apply", "check_status"}:
        preferred.append("application_portal")
    if domain == "employment" and intent in {"discover", "find_job", "check_availability", "apply"}:
        preferred.extend(["official_employment", "student_employment", "graduate_assistantships", "career_center", "employment_portals"])
    return list(dict.fromkeys([*preferred, *groups]))


def compile_campus_query(question: str) -> CampusQuery:
    original = (question or "").strip()
    normalized, correction_reasons = _apply_known_misspellings(_normalize(original))
    scores = _domain_scores(normalized)
    top_score, domain, phrase = scores[0] if scores else (0.0, "general_campus", "")

    detected_intent, action, intent_reason = _detect_intent(normalized, domain)
    schedule_conflict = bool(
        re.search(r"\b(?:find|show|list|which|all)\b", normalized)
        and re.search(
            r"\b(?:do not|don't|won't|will not|without)\s+(?:conflict|overlap)|"
            r"\bnonconflicting\b|\bnot\s+overlap",
            normalized,
        )
        and re.search(r"\b(?:courses?|classes?|sections?|computer science)\b", normalized)
    )
    administrative_schedule_issue = bool(
        not schedule_conflict
        and re.search(r"\b(?:classes?|courses?|sections?|lectures?)\b", normalized)
        and (
            re.search(r"\b(?:same|overlapping)\s+time\b", normalized)
            or re.search(r"\b(?:time|schedule|class)\s+conflict\b", normalized)
            or re.search(r"\b(?:overlap|collide|clash)\w*\b", normalized)
        )
    )
    advisor_workflow = bool(
        re.search(r"\b(?:academic\s+)?(?:advisor|adviser)\b|\b(?:advises|advising)\s+me\b", normalized)
        and re.search(
            r"\b(?:don't|do not|not)\s+know\b|\bfind\b|\bidentify\b|\bwho\b|"
            r"\blocate\b|\bshow\b",
            normalized,
        )
    )
    academic_deadline = bool(
        (
            re.search(r"\b(?:last day|last date|deadline|due date)\b", normalized)
            or re.search(r"\bavoid\s+(?:an\s+)?f\b", normalized)
        )
        and re.search(r"\b(?:drop|withdraw|leave|register|registration|class|course)\b", normalized)
    )
    registrar_compound = bool(
        re.search(r"\bregistrar(?:'s)?(?: office)?\b", normalized)
        and sum(
            bool(re.search(pattern, normalized))
            for pattern in (r"\bwhere\b|\blocation\b", r"\bhours?\b|\bopen\b|\bclose[sd]?\b", r"\bcontact\b|\bphone\b|\bemail\b")
        ) >= 2
    )
    health_help = bool(
        re.search(
            r"\b(?:sick|ill|unwell|injured|medical (?:help|care)|health services?|"
            r"campus clinic|see (?:a )?(?:doctor|nurse)|check me out|"
            r"someone .{0,20}(?:check|treat|examine) me)\b",
            normalized,
        )
    )
    lost_id = bool(
        re.search(r"\b(?:student|mcneese)?\s*id card\b|\bcowboy card\b", normalized)
        and re.search(r"\b(?:lost|replace|replacement|missing|stolen)\b", normalized)
    )
    parking_operation = bool(
        re.search(r"\b(?:parking|campus)\s+(?:ticket|citation|permit)\b", normalized)
        or ("parking" in normalized and "appeal" in normalized)
        or bool(
            re.search(r"\b(?:ticket|citation)\b", normalized)
            and re.search(r"\b(?:windshield|appeal|challenge|contest|dispute)\b", normalized)
        )
    )
    expiring_i20 = bool(
        re.search(r"\bi-?20\b", normalized)
        and re.search(r"\b(?:expir|end date|complete|graduate|extension)\w*\b", normalized)
    )
    international_status_document = bool(
        re.search(r"\binternational (?:student|scholar)\b", normalized)
        and re.search(
            r"\b(?:i-?20|visa|immigration|status|paperwork|document|study in (?:the )?"
            r"(?:united states|u\.?s\.?))\b",
            normalized,
        )
    )
    # Capability meaning outranks lexical campus topics and must never retrieve.
    if detected_intent in {"capability_discovery", "source_trust_explanation", "help_examples"}:
        domain = "capability_discovery"
        top_score = max(top_score, 15.0)
        phrase = detected_intent
    elif academic_deadline:
        domain = "academic_calendar"
        detected_intent, action = "check_deadline", "check"
        top_score = max(top_score, 15.0)
        phrase = "academic registration deadline"
    elif advisor_workflow:
        domain = "registration"
        detected_intent, action = "find_process", "identify_advisor"
        top_score = max(top_score, 15.0)
        phrase = "academic advisor identification workflow"
    elif administrative_schedule_issue:
        domain = "registration"
        detected_intent, action = "find_process", "resolve_schedule_conflict"
        top_score = max(top_score, 15.0)
        phrase = "administrative class-schedule conflict workflow"
    elif schedule_conflict:
        domain = "registration"
        detected_intent, action = "find_process", "calculate"
        top_score = max(top_score, 15.0)
        phrase = "structured course-schedule conflict computation"
    elif health_help:
        domain = "wellbeing"
        detected_intent, action = "locate", "locate"
        top_score = max(top_score, 15.0)
        phrase = "campus medical or health-service request"
    elif lost_id:
        domain = "registration"
        detected_intent, action = "find_process", None
        top_score = max(top_score, 15.0)
        phrase = "student identification replacement process"
    elif parking_operation:
        parking_appeal = bool(
            re.search(r"\b(?:appeal|challenge|contest|dispute)\b", normalized)
        )
        domain = "locations"
        detected_intent, action = (
            ("find_form", "appeal") if parking_appeal
            else ("find_contact", "contact")
        )
        top_score = max(top_score, 15.0)
        phrase = "parking or citation operation"
    elif international_status_document:
        domain = "international_services"
        detected_intent, action = "find_process", "contact"
        top_score = max(top_score, 15.0)
        phrase = "international student status-document workflow"
    elif detected_intent == "navigate" and re.search(r"\b(?:book|textbook|novel)\b", normalized) and re.search(r"\b(?:buy|purchase|order|get|find|copy)\b", normalized):
        domain = "student_services"
        top_score = max(top_score, 12.0)
        phrase = "book purchase or availability operation"
    elif detected_intent == "identify_person":
        domain = "directory"
        top_score = max(top_score, 12.0)
        phrase = "person or campus-leadership identity"
    # A form is an action-record domain even when the form concerns a policy.
    elif detected_intent == "find_course":
        domain = "catalog"
        top_score = max(top_score, 12.0)
        phrase = "course-code or course-record operation"
    elif detected_intent == "find_form":
        domain = "forms"
        top_score = max(top_score, 12.0)
        phrase = "form action"
    elif re.search(r"\binternational\b", normalized) and re.search(
        r"\b(?:apply|admission|applicant|documents?|transcripts?|english test|toefl|ielts|duolingo|submit)\b",
        normalized,
    ):
        domain = "admissions"
        top_score = max(top_score, 12.0)
        phrase = "international admissions operation"

    locked_intents = {
        "identify_person",
        "find_course",
        "capability_discovery",
        "source_trust_explanation",
        "help_examples",
        "navigate",
    }
    # Full-spectrum A-Z taxonomy can specialize the pack when aliases are strong.
    spectrum_probe_intent = _supported_intent(domain, detected_intent, normalized)
    use_spectrum = (
        domain != "capability_discovery"
        and detected_intent not in locked_intents
        and not any((academic_deadline, schedule_conflict, administrative_schedule_issue, advisor_workflow, health_help, lost_id, parking_operation, expiring_i20, international_status_document))
    )
    spectrum = (
        build_full_spectrum_plan(normalized, campus_intent=spectrum_probe_intent)
        if use_spectrum
        else None
    )
    protected_packs = {
        "degree_requirements",
        "catalog",
        "directory",
        "forms",
        "capability_discovery",
        "academic_calendar",
    }
    if spectrum and spectrum.category_id and spectrum.canonical_pack:
        spectrum_pack = spectrum.canonical_pack
        # Do not let a department/office alias steal a stronger specialized pack
        # (for example Computer Science requirements → degree_requirements).
        if domain in protected_packs and top_score >= 5.0 and spectrum_pack != domain:
            should_override = False
        else:
            should_override = spectrum.match_score >= 8.0 or (
                spectrum.match_score >= 5.5
                and (top_score < 6.0 or spectrum_pack == domain)
            )
        if should_override and get_domain_pack(spectrum_pack):
            domain = spectrum_pack
            top_score = max(top_score, spectrum.match_score)
            phrase = spectrum.aliases_hit or spectrum.category or phrase

    intent = _supported_intent(domain, detected_intent, normalized)
    pack = get_domain_pack(domain) or get_domain_pack("general_campus") or {}
    defaults = (pack.get("intent_defaults") or {}).get(intent)
    if defaults is None:
        fallback_intent = next(iter(pack.get("intent_defaults") or {"explain": {"freshness":"static","risk":"low","answer_shape":"short_explanation","required_fields":["answer"]}}))
        intent = fallback_intent
        defaults = pack["intent_defaults"][fallback_intent]
    # Re-plan corpus phrases with the final campus intent.
    spectrum = build_full_spectrum_plan(normalized, campus_intent=intent) if use_spectrum else None
    audience, audience_reason = _audience(normalized)
    subdomain = _subdomain(domain, normalized)
    entities = _entities(normalized, domain, subdomain)
    if spectrum and spectrum.seed_entity and not entities.get("office"):
        entities["office"] = spectrum.seed_entity
    freshness = defaults["freshness"]
    risk = defaults["risk"]
    personal = bool(re.search(r"\bmy (?:application status|status|account|balance|bill|grades?|schedule|degree progress|transcript status)\b", normalized))
    if personal:
        freshness = "personal"
        risk = "high"
    if spectrum and spectrum.risk_level in {"medium", "high"} and risk != "high":
        risk = spectrum.risk_level
    if spectrum and spectrum.freshness_class in {"hourly", "daily"} and freshness not in {"personal", "live"}:
        freshness = "live"
    volatile_parents = {
        "Careers and Employment",
        "Housing and Dining",
        "Athletics and Recreation",
        "Arts, Culture, and Events",
        "Health and Wellness",
        "Safety, Rights, and Compliance",
        "Financial Aid and Scholarships",
        "Business and Finance",
    }
    volatile_intents = {
        "discover",
        "check_availability",
        "find_job",
        "find_event",
        "check_deadline",
        "calculate",
        "apply",
        "list",
    }
    if (
        spectrum
        and spectrum.parent_domain in volatile_parents
        and intent in volatile_intents
        and freshness not in {"personal", "live"}
    ):
        freshness = "live"
    groups = _source_groups(domain, subdomain, intent, pack)
    required_fields = list(defaults.get("required_fields") or [])
    answer_shape = defaults["answer_shape"]
    if schedule_conflict:
        required_fields = ["term", "subject", "constraint_course"]
        answer_shape = "schedule_conflict_result"
    elif lost_id:
        required_fields = ["replacement_process", "replacement_location", "replacement_fee"]
        answer_shape = "policy_plus_steps"
        groups = ["student_id_cards"]
    elif registrar_compound:
        required_fields = ["location", "hours", "contact_method"]
        groups = ["registration", "official_directory"]
    elif advisor_workflow:
        required_fields = ["advisor_identification_steps", "contact_method"]
        answer_shape = "steps_with_contact"
        groups = ["academic_advising"]
    elif administrative_schedule_issue:
        required_fields = ["resolution_options", "contact_method"]
        answer_shape = "policy_plus_steps"
        groups = ["registration", "official_directory"]
    elif health_help:
        required_fields = ["services", "location", "contact_method", "hours", "emergency_guidance"]
        answer_shape = "service_access_card"
        groups = ["health_services"]
    elif parking_operation:
        required_fields = ["steps", "contact_method"]
        answer_shape = "policy_plus_steps"
        groups = ["parking_transportation"]
    elif expiring_i20 or international_status_document:
        required_fields = ["current_student_guidance", "contact_method"]
        answer_shape = "policy_plus_steps"
        groups = ["international_services"]
    if spectrum and spectrum.answer_schema:
        answer_shape = answer_shape_for_schema(spectrum.answer_schema, answer_shape)
    live_needed = requires_live_discovery(
        domain=domain,
        freshness=freshness,
        freshness_class=(spectrum.freshness_class if spectrum else None),
        answer_shape=answer_shape,
    )
    ambiguities: list[str] = []
    clarification_required = False
    if domain == "general_campus" and top_score < 2.5:
        ambiguities.append("No specific campus domain reached the deterministic confidence threshold.")
    if domain == "admissions" and intent == "find_requirements" and audience == "unknown" and re.search(r"\bmy\b|\bi\b", normalized):
        ambiguities.append("Applicant type can materially change admission requirements.")
        clarification_required = top_score < 8.0
    explicit_term_period = bool(
        re.search(
            r"\b(?:fall|spring|summer|winter)\s+20\d{2}\b|"
            r"\b(?:this|current)\s+(?:term|semester|session)\b",
            normalized,
        )
    )
    if (
        domain == "academic_calendar"
        and intent == "check_deadline"
        and (not entities.get("term") or not explicit_term_period)
    ):
        ambiguities.append("The requested academic term and year are not explicit.")
        clarification_required = True
    if domain == "directory" and intent == "identify_person":
        person_name = str(entities.get("person") or "").strip()
        if person_name and len(person_name.split()) < 2:
            ambiguities.append(
                f"Which Dr. {person_name.title()} do you mean? Please share a last name, department, or course."
            )
            clarification_required = True

    runner_up = scores[1][0] if len(scores) > 1 else 0.0
    margin = max(top_score - runner_up, 0.0)
    confidence = min(0.99, max(0.35, 0.45 + min(top_score, 16.0) / 32.0 + min(margin, 6.0) / 30.0))
    if spectrum and spectrum.category_id:
        confidence = max(confidence, min(0.97, 0.55 + min(top_score, 16.0) / 40.0))
    if clarification_required:
        confidence = min(confidence, 0.69)
    reasons = [
        *correction_reasons,
        f"domain {domain} matched configured phrase {phrase!r}",
        intent_reason,
        f"intent resolved to supported operation {intent}",
        f"freshness/risk/answer shape loaded from {domain}.{intent}",
        *list(spectrum.decision_reasons if spectrum else ()),
    ]
    if audience_reason:
        reasons.append(audience_reason)
    if personal:
        reasons.append("personal-record cue requires authenticated data boundary")
    if live_needed:
        reasons.append("full-spectrum freshness/answer shape requires live discovery")
    planned_payload = [
        {
            "query_id": item.query_id,
            "query": item.query,
            "intent": item.intent,
            "source_mode": item.source_mode,
            "preferred_domains": list(item.preferred_domains),
            "answer_schema": item.answer_schema,
            "freshness_class": item.freshness_class,
            "priority_score": item.priority_score,
            "risk_level": item.risk_level,
            "seed_entity": item.seed_entity,
        }
        for item in (spectrum.planned_queries if spectrum else ())
    ]
    return CampusQuery(
        original_query=original,
        normalized_query=normalized,
        domain=domain,
        subdomain=subdomain,
        intent=intent,
        action=action,
        entities=entities,
        audience=audience,
        freshness=freshness,
        risk=risk,
        answer_shape=answer_shape,
        required_source_groups=groups,
        required_fields=required_fields,
        confidence=round(confidence, 3),
        ambiguities=ambiguities,
        clarification_required=clarification_required,
        decision_reasons=reasons,
        category_id=spectrum.category_id if spectrum else None,
        category=spectrum.category if spectrum else None,
        parent_domain=spectrum.parent_domain if spectrum else None,
        subcategory_id=spectrum.subcategory_id if spectrum else None,
        subcategory=spectrum.subcategory if spectrum else None,
        research_intent=spectrum.research_intent if spectrum else None,
        preferred_domains=list(spectrum.preferred_domains) if spectrum else [],
        answer_schema=spectrum.answer_schema if spectrum else None,
        freshness_class=spectrum.freshness_class if spectrum else None,
        seed_entity=spectrum.seed_entity if spectrum else None,
        planned_queries=planned_payload,
        source_policy_ids=list(spectrum.source_policy_ids) if spectrum else [],
        requires_live_discovery=live_needed,
    )


def is_product_self_knowledge_question(question: str) -> bool:
    """Return True only for explicit questions about AskMcNeese itself."""
    normalized = _normalize(question)
    for intent, patterns in _INTENT_PATTERNS[:3]:
        if intent in {"capability_discovery", "source_trust_explanation", "help_examples"}:
            if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
                return True
    return False


def clear_compiler_caches() -> None:
    _misspellings.cache_clear()
    clear_full_spectrum_caches()




