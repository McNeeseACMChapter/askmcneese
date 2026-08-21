"""Conversation awareness for follow-up prompts.

History is already sent by the frontend. This module turns prior turns into a
retrieval-ready question so classify/compile/hybrid are not blind to context.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


CAMPUS_TIMEZONE = "America/Chicago"


# Match anywhere in short questions (not only at start).
_FOLLOWUP_CUES = re.compile(
    r"(?:"
    r"^\s*(?:and|also|but)\b|\bwhat about\b|\bhow about\b|"
    r"\btell me more\b|\bcontinue\b|\bgo on\b|"
    r"\bwhy(?: did you)? stop(?:ped)?\b|\bwhy\b|"
    r"\bwhere exactly\b|\bhow much\b|\bwho should i (?:email|contact)\b|"
    r"\bthe same\b|\bsame (?:place|office|one|program|major|degree)\b|"
    r"\bthat one\b|\bthis one\b|\bmore details?\b|"
    r"\bwhere(?:'s| is) that\b|\bwho(?:'s| is) that\b|\bwhen(?:'s| is) that\b|"
    r"\bcan you also\b|\balso tell\b|\bfor (?:that|this|the same)\b|"
    r"\bin (?:that|this|the same)\b"
    r")",
    re.I,
)
_PRONOUNS = re.compile(
    r"\b(?:it|that|this|they|them|those|there|their|its|same)\b",
    re.I,
)


def build_request_context(
    query: str,
    *,
    conversation_id: str | None = None,
    turn_id: str | None = None,
    parent_turn_id: str | None = None,
    request_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build deterministic campus and turn context before classification."""
    campus_zone = ZoneInfo(CAMPUS_TIMEZONE)
    current = now.astimezone(campus_zone) if now else datetime.now(campus_zone)
    return {
        "request_id": request_id,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "parent_turn_id": parent_turn_id,
        "campus_timezone": CAMPUS_TIMEZONE,
        "current_datetime": current.isoformat(),
        "current_date": current.date().isoformat(),
        "current_day": current.strftime("%A"),
        "query": (query or "").strip(),
    }
_DEGREE_FOLLOWUP_CUES = re.compile(
    r"\b(?:"
    r"400[- ]?level|300[- ]?level|300\s*/\s*400|upper[- ]division|"
    r"electives?|core courses?|general education|gen ed|"
    r"credit hours?|credits?|classes?|courses?"
    r")\b",
    re.I,
)
_PROGRAM_HISTORY_CUES = re.compile(
    r"\b(?:"
    r"computer science|mechanical engineering|electrical engineering|"
    r"civil engineering|nursing|biology|chemistry|psychology|accounting|"
    r"degree plan|curriculum|major|concentration|bachelor|undergraduate|"
    r"catalog|credit hours?"
    r")\b",
    re.I,
)
_SERVICE_HISTORY_CUES = re.compile(
    r"\b(?:"
    r"housing|residence life|dining|parking|handshake|career(?: services)?|"
    r"financial aid|admissions?|scholarship|tuition|registrar|bookstore|"
    r"counseling|health services|library|student employment|jobs?"
    r")\b",
    re.I,
)
_STICKY_TOPIC_RE = re.compile(
    r"\b(?:"
    r"CSCI|calculus\s+II|class planner|"
    r"computer science|mechanical engineering|electrical engineering|"
    r"civil engineering|chemical engineering|engineering technology|"
    r"nursing|biology|chemistry|psychology|accounting|finance|"
    r"business administration|criminal justice|education|"
    r"campus housing|residence life|dining|parking|handshake|"
    r"career services|financial aid|admissions|scholarships?|"
    r"student employment|graduate assistantships?"
    r")\b",
    re.I,
)
_SLOT_TERM_RE = re.compile(
    r"^\s*(?:(?:the|this|for)\s+)?(?:fall|spring|summer|winter|autumn)"
    r"(?:\s+(?:semester|session|term))?(?:\s+20\d{2})?\s*$",
    re.I,
)
_SLOT_YEAR_RE = re.compile(r"^\s*20\d{2}\s*$")
_SLOT_CRN_RE = re.compile(r"^\s*(?:crn\s*)?\d{5}\s*$", re.I)
_SLOT_CONFIRM_RE = re.compile(
    r"^\s*(?:yes|no|yeah|yep|nope|ok|okay|that one|this one|the same|same one)\s*$",
    re.I,
)
_QUESTION_WORD_RE = re.compile(r"\b(?:what|where|when|which|who|how|why)\b", re.I)
_TOPIC_BEARING = re.compile(
    r"\b(?:"
    r"CSCI|calculus(?:\s+II)?|class planner|CRN|"
    r"computer science|engineering|nursing|biology|major|degree|program|"
    r"housing|parking|dining|career|handshake|admissions?|scholarship|"
    r"tuition|financial aid|job|employment|catalog|curriculum|"
    r"library|permit|transcript|meal plan"
    r")\b",
    re.I,
)
_GENERIC_CONTENT = {
    "mcneese", "state", "university", "please", "what", "where", "when",
    "which", "does", "have", "with", "from", "that", "this", "about",
    "available", "offered", "campus",
}
_ENTITY_SWITCH_GENERIC = {
    "close", "closes", "closing", "contact", "department", "hours", "office",
    "open", "services", "time", "today", "tomorrow",
}


def normalize_source_scope(source_scope: str | None, *, use_web_search: bool = False) -> str:
    scope = (source_scope or "").strip().lower()
    if scope in {"adaptive", "knowledge", "web"}:
        return scope
    return "web" if use_web_search else "knowledge"


def _recent_user_questions(history: list[dict[str, Any]] | None, *, limit: int = 5) -> list[str]:
    if not history:
        return []
    out: list[str] = []
    for turn in reversed(history):
        if turn.get("role") != "user":
            continue
        content = str(turn.get("content") or "").strip()
        if content:
            out.append(content)
        if len(out) >= limit:
            break
    return list(reversed(out))


def _history_blob(history: list[dict[str, Any]] | None) -> str:
    if not history:
        return ""
    return " ".join(str(turn.get("content") or "") for turn in history[-8:])


def _extract_sticky_topics(history: list[dict[str, Any]] | None) -> list[str]:
    """Pull durable topics from recent user + assistant turns."""
    if not history:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for turn in history[-8:]:
        text = str(turn.get("content") or "")
        for match in _STICKY_TOPIC_RE.finditer(text):
            topic = re.sub(r"\s+", " ", match.group(0)).strip()
            key = topic.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(topic)
    return found


def _content_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]{4,}", (text or "").lower())
        if token not in _GENERIC_CONTENT
    }


def _is_standalone_new_question(
    question: str,
    history: list[dict[str, Any]] | None,
    task_state: dict[str, Any] | None = None,
) -> bool:
    """True when the new prompt already names a different campus task."""
    q = (question or "").strip()
    if not _QUESTION_WORD_RE.search(q):
        return False
    tokens = _content_tokens(q)
    prior = " ".join(_recent_user_questions(history)[-2:])
    anchor = str((task_state or {}).get("query_anchor") or "")
    prior_tokens = _content_tokens(f"{prior} {anchor}")
    if re.search(r"\b(?:office|department|student services)\b", q, re.I):
        named_entity_terms = (tokens - prior_tokens) - _ENTITY_SWITCH_GENERIC
        if named_entity_terms:
            # "What about the International Office?" is a new named entity,
            # even though "what about" is normally a follow-up cue.
            return True
    if len(tokens) < 3:
        return False
    novel = tokens - prior_tokens
    return len(novel) >= 2


def _topics_for_followup(question: str, topics: list[str]) -> list[str]:
    """Prefer program topics for curriculum follow-ups, services for campus-service ones."""
    if not topics:
        return []
    if _DEGREE_FOLLOWUP_CUES.search(question):
        program_topics = [
            topic
            for topic in topics
            if _PROGRAM_HISTORY_CUES.search(topic)
            and not _SERVICE_HISTORY_CUES.search(topic)
        ]
        return program_topics
    if _SERVICE_HISTORY_CUES.search(question) and not _DEGREE_FOLLOWUP_CUES.search(question):
        service_topics = [topic for topic in topics if _SERVICE_HISTORY_CUES.search(topic)]
        if service_topics:
            return service_topics
    return topics


def _topic_bearing_anchor(prior_users: list[str], topics: list[str]) -> str:
    """Prefer the latest user question that still carries the conversation topic."""
    if not prior_users:
        return ""
    for question in reversed(prior_users):
        q_lower = question.lower()
        if any(topic.lower() in q_lower for topic in topics):
            return question
        if topics and _TOPIC_BEARING.search(question):
            # Only accept a generic topic-bearing turn when it overlaps preferred topics.
            continue
        if not topics and _TOPIC_BEARING.search(question):
            return question
    for question in reversed(prior_users):
        if _TOPIC_BEARING.search(question):
            return question
    return prior_users[-1]


def looks_like_slot_value(
    question: str,
    task_state: dict[str, Any] | None = None,
) -> bool:
    """True only when the new text can fill the pending task slot."""
    q = (question or "").strip()
    if not q:
        return False
    if re.search(r"(?<!\d)\d{5}(?!\d)", q) and len(q.split()) <= 18:
        return True
    if len(q.split()) > 8:
        return False
    if (
        _SLOT_TERM_RE.match(q)
        or _SLOT_YEAR_RE.match(q)
        or _SLOT_CRN_RE.match(q)
        or _SLOT_CONFIRM_RE.match(q)
    ):
        return True
    pending = str((task_state or {}).get("pending_field") or "")
    if (
        pending in {"clarification", "audience", "term", "constraint_section"}
        and len(q.split()) <= 5
        and not _QUESTION_WORD_RE.search(q)
    ):
        return True
    return False


def looks_like_followup(
    question: str,
    history: list[dict[str, Any]] | None,
    task_state: dict[str, Any] | None = None,
) -> bool:
    """Use prior turns only when the new prompt explicitly depends on them."""
    q = (question or "").strip()
    if not q:
        return False
    state_status = str((task_state or {}).get("status") or "")
    if state_status == "awaiting_input":
        # Pending slots accept term/CRN/yes answers. Unrelated language,
        # including a new question, must reset the prior task.
        return looks_like_slot_value(q, task_state)
    if task_state and state_status in {
        "active", "awaiting_input", "blocked", "ready_for_confirmation"
    }:
        if len(q.split()) <= 18 and (
            _FOLLOWUP_CUES.search(q)
            or _PRONOUNS.search(q)
            or re.search(r"(?<!\d)\d{5}(?!\d)", q)
        ):
            return True
    words = q.split()
    if (
        history
        and len(words) <= 12
        and _DEGREE_FOLLOWUP_CUES.search(q)
        and _PROGRAM_HISTORY_CUES.search(_history_blob(history))
        and not _TOPIC_BEARING.search(q)
    ):
        return True
    if _is_standalone_new_question(q, history, task_state):
        return False
    if not history:
        return False
    if len(words) <= 18 and re.search(r"(?<!\d)\d{5}(?!\d)", q):
        return True
    if len(words) <= 18 and re.search(r"\b(?:put|add|save)\b.{0,40}\bclass planner\b", q, re.I):
        return True
    if len(words) <= 18 and _FOLLOWUP_CUES.search(q):
        return True
    if len(words) <= 14 and _PRONOUNS.search(q) and not _TOPIC_BEARING.search(q):
        return True
    return False

def resolve_question_with_history(
    question: str,
    history: list[dict[str, Any]] | None,
    task_state: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return a standalone retrieval question plus context metadata."""
    original = (question or "").strip()
    prior_users = _recent_user_questions(history)
    all_topics = _extract_sticky_topics(history)
    meta: dict[str, Any] = {
        "original_question": original,
        "followup": False,
        "prior_user_questions": prior_users[-3:],
        "sticky_topics": all_topics[-4:],
        "task_state_used": False,
    }
    if not original:
        return original, meta
    # Normalize common typo before follow-up / classification decisions.
    original = re.sub(r"\bhow\s+man\b", "how many", original, flags=re.I)
    meta["original_question"] = original
    state_status = str((task_state or {}).get("status") or "")
    state_active = state_status in {
        "active", "awaiting_input", "blocked", "ready_for_confirmation"
    }
    if state_active and looks_like_followup(original, history, task_state):
        task_type = str(task_state.get("task_type") or "")
        if task_type == "course_schedule_conflict":
            term = str(task_state.get("term") or "").strip()
            subject = str(task_state.get("subject") or "").strip()
            constraint_course = str(task_state.get("constraint_course") or "").strip()
            crns = re.findall(r"(?<!\d)(\d{5})(?!\d)", original)
            constraint_crn = crns[0] if crns else str(task_state.get("constraint_section") or "").strip()
            if term and subject and constraint_course:
                parts = [
                    f"Find {subject} courses in {term} that do not conflict with {constraint_course}."
                ]
                if constraint_crn:
                    parts.append(f"Selected constraint CRN {constraint_crn}.")
                parts.append(f"Current user input: {original}")
                resolved = " ".join(parts)
                meta.update({
                    "followup": True,
                    "resolved_question": resolved,
                    "task_state_used": True,
                    "task_type": task_type,
                })
                return resolved, meta
        anchor = str(task_state.get("query_anchor") or "").strip()
        if anchor:
            resolved = f"{original} (continuing the {task_type or 'campus'} task: {anchor[:240]})"
            meta.update({
                "followup": True,
                "resolved_question": resolved,
                "task_state_used": True,
                "task_type": task_type or None,
            })
            return resolved, meta
    if not looks_like_followup(original, history, task_state) or not prior_users:
        return original, meta

    topics = _topics_for_followup(original, all_topics)
    anchor = _topic_bearing_anchor(prior_users, topics)
    follow_up = original
    if re.search(r"\b400[- ]?level\b", follow_up, re.I) and not re.search(
        r"\b300\s*/\s*400\b", follow_up, re.I
    ):
        follow_up = (
            f"{follow_up} (upper-division 300/400-level credit hours required "
            "for this degree plan)"
        )

    sticky = topics[-1] if topics else (all_topics[-1] if all_topics else "")
    # One-line retrieval query: keep the prior topic visible to classifiers
    # without burying the follow-up behind a multiline string.
    parts = [follow_up]
    if sticky and sticky.lower() not in follow_up.lower():
        parts.append(f"about {sticky}")
    if anchor and anchor.lower() not in follow_up.lower():
        # Keep the anchor short so search APIs stay focused.
        anchor_snip = re.sub(r"\s+", " ", anchor).strip()
        if len(anchor_snip) > 140:
            anchor_snip = anchor_snip[:137].rstrip() + "..."
        parts.append(f"(continuing from: {anchor_snip})")
    # Backward-compatible fallback for clients that have not yet persisted typed
    # task state. Infer only the interaction slot (the chosen constraint CRN),
    # never section facts or compatibility. The Class Planner store rehydrates it.
    schedule_anchor_index = next(
        (
            index
            for index, prior in enumerate(prior_users)
            if re.search(r"\b(?:conflict|overlap)\w*\b", prior, re.I)
            and re.search(r"\b(?:course|class|section)\w*\b", prior, re.I)
        ),
        None,
    )
    if schedule_anchor_index is not None:
        schedule_anchor = prior_users[schedule_anchor_index]
        if not re.search(r"\b(?:conflict|overlap)\w*\b", " ".join(parts), re.I):
            parts.append(f"(schedule task: {schedule_anchor[:140]})")
        constraint_crn = None
        for prior in prior_users[schedule_anchor_index + 1 :]:
            matches = re.findall(r"(?<!\d)(\d{5})(?!\d)", prior)
            if len(matches) == 1:
                constraint_crn = matches[0]
                break
        if constraint_crn and constraint_crn not in follow_up:
            parts.append(f"(selected constraint CRN {constraint_crn})")
        if re.search(r"\b(?:put|add|save)\b.{0,50}\bclass planner\b", follow_up, re.I):
            for prior in reversed(prior_users[schedule_anchor_index + 1 :]):
                selected = list(dict.fromkeys(re.findall(r"(?<!\d)(\d{5})(?!\d)", prior)))
                if len(selected) < 2:
                    continue
                subject = "target"
                try:
                    from app.services.campus_intelligence.compiler import compile_campus_query

                    compiled_anchor = compile_campus_query(prior_users[schedule_anchor_index])
                    subject = str(compiled_anchor.entities.get("subject") or subject)
                except Exception:
                    pass
                parts.append(f"(selected {subject} CRNs {', '.join(selected)})")
                break
    resolved = " ".join(parts)

    meta.update(
        {
            "followup": True,
            "anchor_question": anchor,
            "resolved_question": resolved,
            "sticky_topic": sticky or None,
        }
    )
    return resolved, meta


def history_as_chat_messages(
    history: list[dict[str, Any]] | None,
    *,
    limit: int = 6,
) -> list[dict[str, str]]:
    """Sanitize prior turns for the answer model."""
    if not history:
        return []
    cleaned: list[dict[str, str]] = []
    for turn in history[-limit:]:
        role = turn.get("role")
        content = str(turn.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        cleaned.append({"role": role, "content": content[:2000]})
    return cleaned
