"""Lightweight multi-intent decomposition for complex Ask questions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.rccs.classify import (
    INTENT_FACULTY_IDENTITY,
    INTENT_FACULTY_RATINGS,
    extract_entities,
)


@dataclass
class SubQuestion:
    text: str
    intent: str
    needs_official: bool = True
    needs_companion_rating: bool = False
    needs_web: bool = False


@dataclass
class DecomposedQuery:
    original: str
    subquestions: list[SubQuestion] = field(default_factory=list)
    entities: list = field(default_factory=list)

    @property
    def search_queries(self) -> list[str]:
        return [sq.text for sq in self.subquestions] or [self.original]


_RATING_BITS = re.compile(
    r"\b(rating|ratings|review|reviews|reviewed|difficulty|would take again|rmp|rate my professor)\b",
    re.I,
)
_COUNT_BITS = re.compile(r"\b(how many|number of|count|# of)\b.*\b(review|rating)s?\b", re.I)
_WHO_BITS = re.compile(r"\b(who is|tell me about|what (?:department|title)|contact|email)\b", re.I)


def decompose_question(question: str) -> DecomposedQuery:
    """Split compound faculty/web questions into actionable sub-queries."""
    q = (question or "").strip()
    entities = extract_entities(q)
    faculty = next((e for e in entities if e.entity_type == "faculty_or_staff"), None)
    name = faculty.normalized_name if faculty else ""

    subs: list[SubQuestion] = []

    wants_rating = bool(_RATING_BITS.search(q) or _COUNT_BITS.search(q))
    wants_who = bool(_WHO_BITS.search(q) or (faculty and not wants_rating))
    # Compound "who + rating"
    if faculty and (" and " in q.lower() or "," in q or wants_rating and wants_who):
        wants_who = True

    if name and (wants_who or not wants_rating):
        subs.append(
            SubQuestion(
                text=f"{name} McNeese faculty department title email",
                intent=INTENT_FACULTY_IDENTITY,
                needs_official=True,
                needs_companion_rating=False,
                needs_web=True,
            )
        )
    if name and wants_rating:
        subs.append(
            SubQuestion(
                text=(
                    f"{name} McNeese Rate My Professors rating difficulty "
                    f"number of ratings would take again"
                ),
                intent=INTENT_FACULTY_RATINGS,
                needs_official=False,
                needs_companion_rating=True,
                needs_web=True,
            )
        )
        if _COUNT_BITS.search(q) or "how many" in q.lower():
            subs.append(
                SubQuestion(
                    text=f"{name} McNeese Rate My Professors how many ratings reviews",
                    intent=INTENT_FACULTY_RATINGS,
                    needs_official=False,
                    needs_companion_rating=True,
                    needs_web=True,
                )
            )

    if not subs:
        subs.append(
            SubQuestion(
                text=q,
                intent="general",
                needs_official=True,
                needs_companion_rating=False,
                needs_web=True,
            )
        )

    return DecomposedQuery(original=q, subquestions=subs, entities=entities)
