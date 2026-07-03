"""Query expansion — turn one raw question into several focused sub-queries.

A single embedding of a broad question ("how do I apply for an international
scholarship") retrieves a single blurry neighborhood and misses the distinct
sub-topics a good answer needs (new-freshman requirements vs. continuing-student
process vs. graduate eligibility vs. deadlines). We expand the question into 2-4
intent-specific sub-queries, retrieve for each, then merge + dedup downstream.

Two backends:
- ``rule`` (default): fast, offline, deterministic — good for tests/CI.
- ``llm``: uses the existing Anthropic client to propose sub-queries.

Set ``QUERY_EXPANSION=llm`` (or ``off``) via env to switch. The original question
is always included as the first sub-query so we never lose the literal intent.
"""

from __future__ import annotations

import os
import re

MAX_SUBQUERIES = int(os.getenv("QUERY_EXPANSION_MAX", "4"))
EXPANSION_MODE = os.getenv("QUERY_EXPANSION", "rule").strip().lower()

_PERSONAS = {
    "freshman": ["freshman", "freshmen", "new student", "incoming", "high school",
                 "first-time", "first time", "beginning"],
    "transfer": ["transfer", "transferring", "transferred"],
    "continuing": ["continuing", "current student", "already enrolled",
                   "upperclassman", "sophomore", "junior", "senior", "renew"],
    "graduate": ["graduate", "grad school", "masters", "master's", "phd",
                 "doctoral"],
    "international": ["international", "foreign", "visa", "abroad", "f-1", "f1"],
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _detect(term_groups: dict[str, list[str]], q: str) -> set[str]:
    found = set()
    for name, terms in term_groups.items():
        if any(t in q for t in terms):
            found.add(name)
    return found


def _dedup_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        key = _norm(it)
        if key and key not in seen:
            seen.add(key)
            out.append(it.strip())
    return out


def _rule_expand(question: str) -> list[str]:
    q = _norm(question)
    subs: list[str] = [question.strip()]

    is_scholarship = any(w in q for w in ("scholarship", "scholarships", "award", "merit"))
    is_aid = any(w in q for w in ("financial aid", "fafsa", "grant", "loan"))
    is_cost = any(w in q for w in ("cost", "tuition", "fee", "fees", "price", "afford"))
    is_admission = any(w in q for w in ("admission", "admissions", "apply", "application", "enroll", "requirements"))
    is_deadline = any(w in q for w in ("deadline", "due date", "when", "date"))

    personas = _detect(_PERSONAS, q)

    if is_scholarship:
        intl = "international " if "international" in personas else ""
        # Cover the persona-specific scholarship intents.
        subs.append(f"new freshman {intl}scholarship requirements GPA test scores award amounts")
        subs.append(f"continuing current student {intl}scholarship application process")
        if "international" in personas or "graduate" in personas:
            subs.append(f"{intl}graduate student scholarship eligibility")
        subs.append("scholarship application deadline priority date")
        if "transfer" in personas:
            subs.append(f"transfer student {intl}scholarship GPA award amounts")

    if is_aid:
        subs.append("FAFSA financial aid application process McNeese")
        subs.append("financial aid grants loans work study eligibility")
        subs.append("financial aid deadline")

    if is_cost:
        subs.append("estimated tuition and fees cost of attendance McNeese")
        subs.append("cost of attendance room and board books")

    if is_admission and not is_scholarship:
        if personas:
            for p in personas:
                subs.append(f"{p} student admission requirements and application steps")
        else:
            subs.append("freshman admission requirements GPA test scores")
            subs.append("transfer student admission requirements")
        subs.append("application deadline for admission")

    if is_deadline and not (is_scholarship or is_aid or is_admission):
        subs.append("application deadline dates by term fall spring")

    # Generic fallback for questions we couldn't classify: add a keyword-focused
    # variant and a "requirements / how to" variant.
    if len(subs) == 1:
        keywords = " ".join(
            w for w in re.findall(r"[a-z0-9']+", q)
            if len(w) > 3 and w not in {"what", "when", "where", "which", "does",
                                        "about", "there", "with", "from", "have",
                                        "mcneese", "university"}
        )
        if keywords:
            subs.append(keywords)
            subs.append(f"how to {keywords}")
            subs.append(f"{keywords} requirements eligibility")

    return _dedup_keep_order(subs)[:MAX_SUBQUERIES]


def _llm_expand(question: str) -> list[str]:
    """Ask the LLM for focused sub-queries. Falls back to rules on any error."""
    try:
        from app.services.llm import _get_client, CLAUDE_MODEL

        client = _get_client()
        prompt = (
            "Break the user's question into 2-4 short, focused search sub-queries "
            "that together cover the likely intents (different student categories, "
            "requirements, process, deadlines). Return ONLY the sub-queries, one per "
            "line, no numbering.\n\nQuestion: " + question
        )
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text if resp.content else ""
        lines = [re.sub(r"^\s*[-*\d.]+\s*", "", ln).strip() for ln in raw.splitlines()]
        subs = [question.strip()] + [ln for ln in lines if ln]
        return _dedup_keep_order(subs)[:MAX_SUBQUERIES]
    except Exception:
        return _rule_expand(question)


def expand_query(question: str, mode: str | None = None) -> list[str]:
    """Return an ordered, deduped list of sub-queries (original first)."""
    if not question or not question.strip():
        return []
    mode = (mode or EXPANSION_MODE).lower()
    if mode == "off":
        return [question.strip()]
    if mode == "llm":
        return _llm_expand(question)
    return _rule_expand(question)
