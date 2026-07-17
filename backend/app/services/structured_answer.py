"""Best-effort structured answer extraction for AskResponse.

Does not invent institutional facts. Only lifts structure already present in
the markdown answer — and only when the answer type / evidence justify sections.
Supporting fields are omitted (None) rather than returned empty.
"""

from __future__ import annotations

import re
from typing import Any


DATE_WORDS = (
    "deadline",
    "due",
    "date",
    "opens",
    "closes",
    "start",
    "end",
    "fall",
    "spring",
    "summer",
    "semester",
)

REQUIREMENT_WORDS = (
    "require",
    "must",
    "gpa",
    "sat",
    "act",
    "transcript",
    "fee",
    "eligibility",
    "document",
    "need",
)

STEP_WORDS = ("step", "first", "next", "then", "finally", "apply", "submit")

REQUIREMENT_QUESTION = (
    "requirement",
    "requirements",
    "eligible",
    "eligibility",
    "what do i need",
    "what documents",
    "documents needed",
    "need to",
)


def _norm(text: str) -> str:
    t = re.sub(r"[#*_`>\-\[\]().,:;!?\"']", " ", (text or "").lower())
    return re.sub(r"\s+", " ", t).strip()


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("**") and s.endswith("**") and len(s) < 120:
            return s.strip("*").strip()
    return None


def _first_paragraph(text: str) -> str:
    parts: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if parts:
                break
            continue
        if s.startswith("#") or s.startswith("```"):
            if parts:
                break
            continue
        if s.startswith("- ") or s.startswith("* ") or re.match(r"^\d+\.\s", s):
            if parts:
                break
            continue
        parts.append(re.sub(r"\*\*|__", "", s))
        if len(" ".join(parts)) > 40:
            break
    return " ".join(parts).strip()


def _bullet_facts(text: str, keywords: tuple[str, ...], limit: int = 6) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^[-*•]\s*\*?\*?([^:*]+)\*?\*?:\s*(.+)$", s)
        if not m:
            m = re.match(r"^\*?\*?([^:*]{2,40})\*?\*?:\s*(.+)$", s)
        if not m:
            continue
        label = re.sub(r"\*\*", "", m.group(1)).strip()
        value = re.sub(r"\*\*", "", m.group(2)).strip()
        if not label or not value:
            continue
        blob = f"{label} {value}".lower()
        if any(k in blob for k in keywords):
            facts.append({"label": label, "value": value})
        if len(facts) >= limit:
            break
    return facts


def _ordered_steps(text: str, limit: int = 8) -> list[str]:
    steps: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\d+\.\s+(.+)$", line.strip())
        if m:
            step = m.group(1).strip()
            if step:
                steps.append(step)
        if len(steps) >= limit:
            break
    return steps


def _warnings(text: str) -> list[str]:
    notes: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith(("note:", "important:", "warning:", "tip:")):
            notes.append(re.sub(r"^(note|important|warning|tip):\s*", "", s, flags=re.I))
    return notes


def _fact_key(fact: dict[str, str]) -> str:
    return _norm(f"{fact.get('label', '')} {fact.get('value', '')}")


def _dedupe_facts(facts: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for fact in facts:
        key = _fact_key(fact)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(fact)
    return out


def infer_answer_type(
    question: str,
    answer: str,
    num_results: int,
    model: str | None,
) -> str:
    if model == "clarification":
        return "clarification"
    if model == "conversational":
        return "conversational"
    if not answer:
        return "backend_failure"
    low_a = answer.lower()
    low_q = question.lower()
    if num_results == 0 and ("couldn't find" in low_a or "no relevant" in low_a or "don't have that" in low_a):
        return "no_source"
    if any(w in low_q for w in ("vs", "versus", "compare", "difference")):
        return "comparison"
    if any(w in low_q for w in ("where", "office", "building", "location", "address", "phone", "email", "contact")):
        return "location"
    if any(w in low_q for w in REQUIREMENT_QUESTION) or (
        any(w in low_q for w in ("require", "eligibility")) and "how" not in low_q[:12]
    ):
        # Prefer requirements intent before date keywords when both appear.
        if _ordered_steps(answer) and any(w in low_q for w in ("how do i", "how to", "steps", "process")):
            return "process"
        return "factual"  # requirements live in arrays; type stays readable
    if _ordered_steps(answer) or any(w in low_q for w in ("how do i", "how to", "steps", "process")):
        return "process"
    # Deadline only from question intent — never from answer body alone
    # (bios with "Fall", "started", "semester" were falsely labeled DEADLINES).
    # Use word boundaries so "date" does not match inside "updated".
    def _has_word(word: str) -> bool:
        return re.search(rf"\b{re.escape(word)}\b", low_q) is not None

    if any(_has_word(w) for w in DATE_WORDS) and any(
        _has_word(w) for w in ("deadline", "due", "when", "date", "closes", "opens", "calendar")
    ):
        return "deadline"
    if num_results > 0 and len(answer) < 280:
        return "factual"
    if num_results > 0:
        return "partial" if num_results < 2 else "factual"
    return "partial"


def _question_wants_requirements(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in REQUIREMENT_QUESTION)


def _question_wants_steps(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in ("how do i", "how to", "steps", "process", "apply for", "change my"))


def _question_wants_dates(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in ("deadline", "due", "when", "date", "closes", "opens", "hours"))


def structure_answer(
    *,
    question: str,
    answer: str,
    num_results: int,
    model: str | None = None,
    confidence: str | None = None,
) -> dict[str, Any]:
    """Return additive structured fields. Never replaces `answer`.

    Supporting sections are omitted unless justified by answer type / question
    intent and non-empty, non-duplicated evidence in the markdown.
    """
    answer_type = infer_answer_type(question, answer, num_results, model)
    title = _first_heading(answer)
    summary = _first_paragraph(answer)

    # Avoid UI double-render: summary often duplicates the opening of content_markdown.
    if summary:
        plain = _norm(answer)
        s_plain = _norm(summary)
        if s_plain and plain.startswith(s_plain[: min(48, len(s_plain))]):
            summary = ""

    # Simple / short answers: direct markdown only — no supporting section soup.
    simple_types = {"factual", "conversational", "clarification", "location", "no_source", "backend_failure"}
    is_short = len(answer.strip()) < 320
    wants_req = _question_wants_requirements(question)
    wants_steps = _question_wants_steps(question) or answer_type == "process"
    wants_dates = _question_wants_dates(question) or answer_type == "deadline"

    important_dates: list[dict[str, str]] | None = None
    requirements: list[str] | None = None
    steps: list[str] | None = None
    warnings: list[str] | None = None
    key_facts: list[dict[str, str]] | None = None  # intentionally unused as default cards

    if answer_type not in {"no_source", "backend_failure", "conversational", "clarification"}:
        date_facts = _dedupe_facts(_bullet_facts(answer, DATE_WORDS))
        req_facts = _dedupe_facts(_bullet_facts(answer, REQUIREMENT_WORDS))
        # Dates win over overlapping requirement/date bullets for the dates section.
        date_keys = {_fact_key(f) for f in date_facts}
        req_facts = [f for f in req_facts if _fact_key(f) not in date_keys]

        if wants_dates and date_facts:
            important_dates = date_facts

        if wants_req and req_facts and len(req_facts) >= 1:
            requirements = [
                f["value"]
                if f["label"].lower().startswith("require")
                else f"{f['label']}: {f['value']}"
                for f in req_facts
            ]
            # Drop requirements that only restate the summary/direct answer.
            if summary:
                s_norm = _norm(summary)
                requirements = [r for r in requirements if _norm(r) not in s_norm and s_norm not in _norm(r)]
            if len(requirements) < 1:
                requirements = None

        ordered = _ordered_steps(answer)
        # Promote steps only for process questions with 2+ real steps.
        if wants_steps and len(ordered) >= 2:
            steps = ordered
        elif wants_steps and len(ordered) == 1 and not is_short:
            # Single step is just a sentence — leave it in the body.
            steps = None

        notes = _warnings(answer)
        if notes:
            warnings = notes

        # Never emit "key facts" card grid for simple factual answers.
        # For long partial/comparison answers, still prefer dates/requirements over generic cards.
        if (
            answer_type in {"comparison", "partial"}
            and not is_short
            and not important_dates
            and not requirements
            and not steps
        ):
            leftovers = _dedupe_facts(_bullet_facts(answer, DATE_WORDS + REQUIREMENT_WORDS))
            if len(leftovers) >= 3:
                key_facts = leftovers[:4]

    # For simple short factual answers, strip all supporting arrays.
    if answer_type in simple_types and is_short and not wants_req and not wants_steps and not wants_dates:
        important_dates = None
        requirements = None
        steps = None
        key_facts = None
        # Keep genuine warnings only.

    if confidence is None:
        if num_results >= 3:
            confidence = "high"
        elif num_results >= 1:
            confidence = "medium"
        else:
            confidence = "low"

    return {
        "answer_type": answer_type,
        "title": title,
        "summary": summary or None,
        "content_markdown": answer,
        "key_facts": key_facts or None,
        "important_dates": important_dates or None,
        "requirements": requirements or None,
        "steps": steps or None,
        "warnings": warnings or None,
        "related_questions": None,
        "confidence": confidence,
    }
