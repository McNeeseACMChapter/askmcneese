"""Independent goal-signal checks that sit above compiler/taxonomy scoring.

Classification can pick a lexically plausible pack whose evidence contract does
not represent the user's goal. This module extracts operational signals from the
user's words and, when they conflict with the compiled route, returns a
domain-general correction. It must not encode one observed question.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from .registry import load_domain_pack_registry


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
_GENERIC = {
    "mcneese", "university", "state", "school", "campus", "question", "please",
    "tell", "give", "need", "want", "help", "about", "with", "what", "where",
    "when", "which", "who", "how", "can", "could", "would", "does", "the",
    "and", "for", "from", "into", "there", "any", "available", "a", "an",
    "are", "at", "by", "do", "i", "in", "is", "it", "me", "my", "of", "on",
    "to", "you", "your", "now", "but", "exact",
}

_CORE_VOCABULARY = {
    "international", "admission", "admissions", "applicant", "application",
    "registrar", "registration", "register", "scholarship", "financial",
    "undergraduate", "graduate", "transfer", "transcript", "immigration",
}

_SERVICE_TERMS = (
    "housing", "dorm", "residence", "dining", "meal", "bookstore", "textbook",
    "novel", "cowboystore",
)
_STATUS_DOC_TERMS = re.compile(
    r"\b(?:i-?20|visa|sevis|f-1|immigration|status document|paperwork)\b"
)
_APPLY_TERMS = re.compile(
    r"\b(?:apply|application|applicant|steps? to apply|how to apply|to apply)\b"
)
_DOCUMENT_TERMS = re.compile(r"\b(?:documents?|transcripts?|toefl|ielts|duolingo)\b")
_REGISTER_TERMS = re.compile(r"\b(?:register|enroll|add a class|registration)\b")
_INTERNATIONAL_TERMS = re.compile(
    r"\b(?:international|foreign student|international student|international applicant)\b"
)


@dataclass(frozen=True)
class GoalSignals:
    international: bool
    apply: bool
    register: bool
    status_documents: bool
    admissions_documents: bool
    campus_service: bool
    tokens: frozenset[str]


@dataclass(frozen=True)
class RouteCorrection:
    domain: str
    intent: str
    action: str | None
    reason: str


def _levenshtein(left: str, right: str, *, limit: int = 2) -> int:
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous = list(range(len(right) + 1))
    for i, left_ch in enumerate(left, start=1):
        current = [i]
        min_row = i
        for j, right_ch in enumerate(right, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (left_ch != right_ch)
            value = min(insert_cost, delete_cost, replace_cost)
            current.append(value)
            if value < min_row:
                min_row = value
        if min_row > limit:
            return limit + 1
        previous = current
    return previous[-1]


@lru_cache(maxsize=1)
def campus_vocabulary() -> frozenset[str]:
    words = set(_CORE_VOCABULARY)
    for pack in load_domain_pack_registry()["packs"].values():
        phrases = list(pack.get("synonyms") or [])
        phrases.extend(pack.get("campus_vocabulary") or [])
        phrases.extend(str(value) for value in (pack.get("common_misspellings") or {}).values())
        for phrase in phrases:
            for token in _TOKEN_RE.findall(str(phrase).lower()):
                if len(token) >= 6 and token not in _GENERIC:
                    words.add(token)
    return frozenset(words)


def clear_route_validator_caches() -> None:
    campus_vocabulary.cache_clear()


def _is_regular_inflection(token: str, word: str) -> bool:
    if token == word:
        return True
    for longer, shorter in ((token, word), (word, token)):
        if longer == f"{shorter}s" or longer == f"{shorter}es":
            return True
        if longer.endswith("ies") and shorter.endswith("y") and longer[:-3] == shorter[:-1]:
            return True
    return False


def correct_campus_spelling(text: str) -> tuple[str, list[str]]:
    """Correct near-miss campus vocabulary without one-off question patches."""
    vocabulary = campus_vocabulary()
    reasons: list[str] = []
    pieces: list[str] = []
    last = 0
    for match in _TOKEN_RE.finditer(text or ""):
        token = match.group(0)
        pieces.append(text[last:match.start()])
        replacement = token
        lowered = token.lower()
        if (
            len(lowered) >= 8
            and lowered not in vocabulary
            and lowered not in _GENERIC
            and not any(_is_regular_inflection(lowered, word) for word in vocabulary)
        ):
            candidates: list[tuple[float, str]] = []
            for word in vocabulary:
                if abs(len(word) - len(lowered)) > 2:
                    continue
                if word[0] != lowered[0]:
                    continue
                distance = _levenshtein(lowered, word)
                ratio = SequenceMatcher(None, lowered, word).ratio()
                if distance <= 2 or ratio >= 0.84:
                    candidates.append((distance + (1.0 - ratio), word))
            candidates.sort()
            if (
                candidates
                and (
                    len(candidates) == 1
                    or candidates[0][0] + 0.15 < candidates[1][0]
                )
            ):
                replacement = candidates[0][1]
                if replacement != lowered:
                    reasons.append(
                        f"normalized campus spelling {lowered!r} to {replacement!r}"
                    )
        pieces.append(replacement)
        last = match.end()
    pieces.append((text or "")[last:])
    return "".join(pieces), reasons


def extract_goal_signals(text: str) -> GoalSignals:
    q = text or ""
    tokens = frozenset(
        token
        for token in _TOKEN_RE.findall(q)
        if len(token) > 1 and token not in _GENERIC
    )
    status_documents = bool(_STATUS_DOC_TERMS.search(q))
    return GoalSignals(
        international=bool(_INTERNATIONAL_TERMS.search(q)),
        apply=bool(_APPLY_TERMS.search(q)),
        register=bool(_REGISTER_TERMS.search(q)),
        status_documents=status_documents,
        admissions_documents=bool(_DOCUMENT_TERMS.search(q)) and not status_documents,
        campus_service=any(term in tokens for term in _SERVICE_TERMS),
        tokens=tokens,
    )


def suggested_operational_route(
    signals: GoalSignals,
    *,
    domain: str,
    intent: str,
) -> RouteCorrection | None:
    """Return a correction only when the compiled route contradicts user signals."""
    if signals.international and signals.status_documents and not signals.apply:
        if domain != "international_services":
            return RouteCorrection(
                domain="international_services",
                intent="find_process",
                action="contact",
                reason="international status-document signals require international_services",
            )
        return None

    if (
        signals.international
        and signals.admissions_documents
        and not signals.apply
        and domain != "admissions"
    ):
        return RouteCorrection(
            domain="admissions",
            intent="find_requirements",
            action=None,
            reason="international admission-document signals require admissions requirements",
        )

    if signals.international and signals.apply:
        if domain == "admissions" and intent in {"apply", "find_requirements", "find_form"}:
            if intent != "apply":
                return RouteCorrection(
                    domain="admissions",
                    intent="apply",
                    action="apply",
                    reason="international application steps require admissions:apply",
                )
            return None
        return RouteCorrection(
            domain="admissions",
            intent="apply",
            action="apply",
            reason="international application steps require admissions:apply",
        )

    if (
        domain == "student_services"
        and not signals.campus_service
        and (signals.apply or signals.register or signals.international)
    ):
        if signals.register and not signals.apply:
            return RouteCorrection(
                domain="registration",
                intent="register",
                action="register",
                reason="class registration signals do not entail housing/dining/bookstore",
            )
        if signals.apply:
            return RouteCorrection(
                domain="admissions",
                intent="apply",
                action="apply",
                reason="application steps do not entail housing/dining/bookstore",
            )
    return None


def route_matches_goal(query: Any, signals: GoalSignals | None = None) -> bool:
    signals = signals or extract_goal_signals(getattr(query, "normalized_query", "") or "")
    return suggested_operational_route(
        signals,
        domain=str(getattr(query, "domain", "") or ""),
        intent=str(getattr(query, "intent", "") or ""),
    ) is None
