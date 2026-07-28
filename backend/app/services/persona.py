"""Persona detection + clarification for applicant-category-dependent questions.

Scholarship, admission, and "how do I apply" answers differ sharply by applicant
category (new freshman vs. transfer vs. continuing vs. graduate, with an
international modifier). Answering all of them generically is exactly what made
responses feel shallow.

Flow used by the /ask router:
1. Detect the persona from the current question and prior conversation.
2. If the topic is category-dependent AND the stage is still unknown, ask ONE
   clarifying question instead of guessing.
3. Otherwise pass the detected persona to the generator so it leads with the
   right category.
"""

from __future__ import annotations

import os
import re

# MVP interim fix: the clarification gate fired on every category-dependent
# question because the frontend historically sent no history, so a first-turn
# "how to apply for international scholarship" was answered with a clarifying
# question instead of the facts. For the MVP we DISABLE the gate and instead let
# the synthesis prompt answer for all applicant categories at once (see
# ``llm._persona_line``). Flip ASKMCNEESE_PERSONA_GATE=1 to re-enable it.
CLARIFICATION_ENABLED = os.getenv("ASKMCNEESE_PERSONA_GATE", "0") == "1"

# Stage keywords (the dimension that most changes the answer).
_STAGE_TERMS: dict[str, list[str]] = {
    "new freshman": ["freshman", "freshmen", "incoming", "new student",
                     "first-time", "first time", "beginning", "high school",
                     "entering", "senior in high school"],
    "transfer": ["transfer", "transferring", "transferred"],
    "continuing student": ["continuing", "current student", "currently enrolled",
                           "already enrolled", "current mcneese", "upperclassman",
                           "sophomore", "junior", "senior", "renew", "renewal",
                           "existing student", "returning"],
    "undergraduate": ["undergraduate", "undergrad"],
    "graduate": ["graduate", "grad school", "grad student", "masters",
                 "master's", "phd", "doctoral", "doctorate"],
}

_INTERNATIONAL_TERMS = ["international", "foreign", "visa", "f-1", "f1", "abroad",
                        "non-us", "non us", "overseas"]

# Topics whose correct answer depends on the applicant category.
_CATEGORY_DEPENDENT = [
    "scholarship", "scholarships", "award", "merit",
    "apply", "application", "admission", "admissions", "admit",
    "requirement", "requirements", "eligibility", "eligible", "enroll",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _detect_stage(text: str) -> str | None:
    t = _norm(text)
    for stage, terms in _STAGE_TERMS.items():
        if any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", t) for term in terms):
            return stage
    return None

def _is_international(text: str) -> bool:
    t = _norm(text)
    return any(term in t for term in _INTERNATIONAL_TERMS)


def _history_text(history: list[dict] | None) -> str:
    if not history:
        return ""
    return " ".join(str(m.get("content", "")) for m in history)


def is_category_dependent(question: str) -> bool:
    t = _norm(question)
    return any(term in t for term in _CATEGORY_DEPENDENT)


def detect_persona(question: str, history: list[dict] | None = None) -> str | None:
    """Return a human-readable persona (e.g. "international new freshman") or None.

    Looks at the current question first, then falls back to conversation history
    so a follow-up ("I'm a transfer student") resolves an earlier ambiguity.
    """
    hist = _history_text(history)
    combined = f"{question} {hist}"

    stage = _detect_stage(question) or _detect_stage(hist)
    international = _is_international(combined)

    if stage and international:
        return f"international {stage}"
    if stage:
        return stage
    if international:
        return "international student"
    return None


def needs_clarification(question: str, history: list[dict] | None = None) -> bool:
    """True when the question is category-dependent but the STAGE is unknown.

    The international modifier alone is not enough â€” "how do I apply for an
    international scholarship" still needs to know new vs. continuing vs. graduate.
    """
    # MVP: gate disabled â€” never block turn 1 with a clarifying question.
    # Campus-intelligence clarification is independent from the optional
    # applicant-persona gate. Ambiguous people/terms should be clarified before
    # retrieval rather than rendered as an internal evidence failure.
    try:
        from app.services.campus_intelligence.compiler import compile_campus_query

        compiled = compile_campus_query(question)
        if compiled.clarification_required and compiled.ambiguities:
            return True
    except Exception:
        pass

    if not CLARIFICATION_ENABLED:
        return False
    if not is_category_dependent(question):
        return False
    stage = _detect_stage(question) or _detect_stage(_history_text(history))
    return stage is None


_CLARIFY_MARKER = "which best describes you?"


def already_clarified(history: list[dict] | None) -> bool:
    """True if we already asked the applicant-category question earlier.

    Prevents an endless clarify loop when the user never states a category.
    """
    if not history:
        return False
    for msg in history:
        assistant_text = _norm(msg.get("content", ""))
        if msg.get("role") == "assistant" and (
            _CLARIFY_MARKER in assistant_text or assistant_text.startswith("which dr.")
        ):
            return True
    return False


def clarification_question(question: str, history: list[dict] | None = None) -> str:
    """Return ONE friendly clarifying question tailored to the topic."""
    try:
        from app.services.campus_intelligence.compiler import compile_campus_query

        compiled = compile_campus_query(question)
        if compiled.clarification_required and compiled.ambiguities:
            return compiled.ambiguities[0]
    except Exception:
        pass

    t = _norm(question)
    intl = _is_international(f"{question} {_history_text(history)}")
    topic = "scholarships" if ("scholarship" in t or "award" in t) else "this"
    intl_note = " (international students have their own award tiers)" if intl else ""
    return (
        f"Happy to help with {topic}! The requirements and amounts depend on your "
        f"applicant category{intl_note}. Which best describes you?\n\n"
        "- New/incoming freshman\n"
        "- Transfer student\n"
        "- Current/continuing McNeese student\n"
        "- Graduate student\n\n"
        "Let me know and I'll give you the exact GPA, award amounts, and deadlines "
        "for your situation."
    )


