"""Intent classification for incoming queries.

Not every message is a knowledge question. Greetings, thanks, and small talk
should be answered conversationally WITHOUT triggering a web search or hitting
the LLM. This keeps the assistant responsive and natural even when the Claude
API is unavailable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    THANKS = "thanks"
    GOODBYE = "goodbye"
    IDENTITY = "identity"       # "who are you", "what can you do"
    QUESTION = "question"        # real knowledge query -> web search
    CHITCHAT = "chitchat"        # generic small talk


@dataclass
class IntentResult:
    intent: Intent
    # A direct reply for conversational intents. Empty for QUESTION.
    reply: str = ""


# Exact-ish greeting tokens
_GREETING_WORDS = {
    "hi", "hello", "hey", "heya", "hiya", "yo", "sup", "howdy",
    "hi there", "hello there", "hey there", "good morning",
    "good afternoon", "good evening", "greetings", "hi!", "hello!",
    "hey!", "morning", "evening",
}

_THANKS_WORDS = {
    "thanks", "thank you", "thx", "ty", "thank u", "appreciate it",
    "thanks!", "thank you!", "much appreciated", "cheers",
}

_GOODBYE_WORDS = {
    "bye", "goodbye", "see you", "see ya", "later", "cya",
    "good night", "goodnight", "take care", "bye!",
}

_IDENTITY_PATTERNS = [
    r"who are you",
    r"what are you",
    r"what can you do",
    r"what do you do",
    r"how do you work",
    r"what is this",
    r"help me",
    r"^help$",
    r"your name",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).strip(" .!?,")


def classify_intent(question: str) -> IntentResult:
    """Classify a query into a conversational intent or a real question."""
    norm = _normalize(question)

    if not norm:
        return IntentResult(
            Intent.GREETING,
            "Hi! I'm AskMcNeese. Ask me anything about McNeese State University — "
            "admissions, programs, financial aid, deadlines, campus life, and more.",
        )

    words = norm.split()
    is_short = len(words) <= 4

    # Greetings — only treat as greeting when the message is short and greeting-led
    if norm in _GREETING_WORDS or (is_short and words[0] in {"hi", "hello", "hey", "heya", "hiya", "yo", "howdy", "sup"}):
        return IntentResult(
            Intent.GREETING,
            "Hey there! I'm AskMcNeese, your assistant for McNeese State University. "
            "You can ask me about admissions, application deadlines, programs, "
            "financial aid, scholarships, tuition, or campus life. What would you like to know?",
        )

    # Thanks
    if norm in _THANKS_WORDS or (is_short and ("thank" in norm or norm in {"thx", "ty"})):
        return IntentResult(
            Intent.THANKS,
            "You're welcome! Is there anything else you'd like to know about McNeese?",
        )

    # Goodbye
    if norm in _GOODBYE_WORDS or (is_short and words[0] in {"bye", "goodbye", "cya"}):
        return IntentResult(
            Intent.GOODBYE,
            "Take care! Come back anytime you have questions about McNeese State University. Go Pokes!",
        )

    # Identity / capabilities
    for pat in _IDENTITY_PATTERNS:
        if re.search(pat, norm):
            return IntentResult(
                Intent.IDENTITY,
                "I'm AskMcNeese, an AI assistant for McNeese State University. "
                "I search the official McNeese website in real time to answer your questions about:\n\n"
                "- Admissions and application deadlines\n"
                "- Undergraduate and graduate programs\n"
                "- Financial aid and scholarships\n"
                "- Tuition and costs\n"
                "- Campus life and student services\n\n"
                "Just ask me a question and I'll find the answer from mcneese.edu.",
            )

    # Everything else is a real question -> web search
    return IntentResult(Intent.QUESTION)
