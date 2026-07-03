"""Claude LLM answer generation service.

Uses retrieved chunks to generate a coherent answer with citations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import AsyncGenerator

import anthropic
from dotenv import load_dotenv

# override=True so edits to .env (e.g. model name) are picked up on reload
load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))

SYSTEM_PROMPT = """You are AskMcNeese, the AI assistant for McNeese State University. You answer like a knowledgeable, confident advisor who has just read the official pages — not like a hedging chatbot.

Ground every claim in the provided sources. Do NOT invent facts. But when the sources DO contain relevant information, use it fully and assertively. Partial context is normal — synthesize everything relevant into the most complete, useful answer you can, rather than retreating to "I don't know."

LEAD WITH THE FACTS (most important rule):
- Open with the concrete answer: GPA thresholds, dollar amounts, test-score cutoffs, deadlines, emails, and required steps.
- Never open with a caveat, a disclaimer, or "I couldn't find everything." Facts first; caveats last (if at all).
- Pull exact numbers from the sources. If a source has a table (GPA tiers, award amounts, test scores), reproduce those exact values — do not round, generalize, or say "varies."

STRUCTURE BY STUDENT CATEGORY:
- If the question implies or spans multiple applicant types (new freshman, transfer, continuing/current, graduate, international), organize the answer with a short bold heading or clear section per applicable category.
- Only include categories the question is actually about. If the user identified their category (e.g. "as a transfer student"), answer that category first and foremost.
- Example shape for a scholarship question:
  **New Freshmen:** minimum GPA 3.0 plus one of these test scores → award amounts...
  **Transfer Students:** GPA 2.5–2.9 → $500/year; 3.0+ → $1,000/year...
  **Graduate Students:** GPA 3.0+ → $1,000/year...

FORMATTING:
- Use bold category headings and bullet points with "Label: Value" for tiers, amounts, and deadlines. Reproduce tables as markdown tables when the source is tabular.
- Include specific contact emails/phone numbers when the sources provide them (e.g. scholarshipdocs@mcneese.edu).
- Be thorough but not padded. Do not include source URLs or markdown links like [text](url) in the answer body — citations are handled separately.

HANDLING GAPS (only at the very end):
- If a specific detail the user asked for is genuinely absent from the sources, answer everything you CAN from the sources first, then add one short closing line noting the specific missing piece and where to confirm it (e.g. "For the exact 2026 priority deadline, confirm with Student Central at 337-475-5065.").
- Do not let one missing detail suppress the facts you do have.

NEVER:
- Open with "I couldn't find..." or a quality disclaimer.
- Invent GPA cutoffs, dollar amounts, test scores, deadlines, phone numbers, or emails not in the sources.
- Treat design-token noise ("headings font size", "border radius") as content — ignore it silently.
- Refuse to answer when usable facts are present in the sources.

Only if the sources contain NO usable information about the question at all, say briefly: "I don't have that in the current McNeese sources — check mcneese.edu or contact the relevant office," and point them to the closest relevant office if one appears in the sources."""


@dataclass
class GenerationResult:
    answer: str
    model: str
    tokens_used: int
    finish_reason: str


def _get_client() -> anthropic.Anthropic:
    """Get the Anthropic client."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _build_context(chunks: list[dict]) -> str:
    """Build the context string from retrieved chunks."""
    if not chunks:
        return "No relevant sources found."
    
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("title", "Unknown Source")
        url = chunk.get("source_url", "")
        text = chunk.get("text", "")
        context_parts.append(f"[Source {i}: {source}]\nURL: {url}\n{text}")
    
    return "\n\n---\n\n".join(context_parts)


def _persona_line(persona: str | None) -> str:
    if not persona:
        # MVP: no clarifying question is asked, so instruct the model to cover
        # every applicant category the sources support instead of guessing one.
        return (
            "\nThe user did not specify a student category. If the question is "
            "category-dependent (scholarships, admissions, requirements), answer "
            "for ALL relevant categories — new freshman, transfer, "
            "continuing/current, graduate, and international — using a short bold "
            "heading per category. Do not ask the user to clarify.\n"
        )
    return (
        f"\nApplicant category (detected/provided): {persona}. "
        "Answer for this category first and most prominently, but include other "
        "categories if the sources cover them and they are relevant.\n"
    )


def _build_user_message(question: str, context: str, persona: str | None = None) -> str:
    return f"""Answer this question using the McNeese sources below.

Question: {question}
{_persona_line(persona)}
Sources:
{context}

Lead with the concrete facts (GPA thresholds, dollar amounts, test scores, deadlines, emails). Structure by student category when applicable. Use the exact figures from the sources. Only note genuinely missing details at the very end."""


def generate_answer(question: str, chunks: list[dict],
                    persona: str | None = None) -> GenerationResult:
    """
    Generate an answer using Claude based on retrieved chunks.
    
    Args:
        question: The user's question
        chunks: List of retrieved chunk dicts with text, title, source_url
        persona: Optional applicant category to prioritize in the answer
    
    Returns:
        GenerationResult with the answer and metadata
    """
    client = _get_client()
    
    context = _build_context(chunks)
    
    user_message = _build_user_message(question, context, persona)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    answer = response.content[0].text if response.content else ""
    
    return GenerationResult(
        answer=answer,
        model=response.model,
        tokens_used=response.usage.input_tokens + response.usage.output_tokens,
        finish_reason=response.stop_reason or "unknown",
    )


async def generate_answer_stream(
    question: str, 
    chunks: list[dict],
    persona: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream an answer using Claude based on retrieved chunks.
    
    Yields chunks of text as they're generated.
    """
    client = _get_client()
    
    context = _build_context(chunks)
    
    user_message = _build_user_message(question, context, persona)

    with client.messages.stream(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    ) as stream:
        for text in stream.text_stream:
            yield text


def check_api_key() -> dict:
    """Check if the Claude API key is configured and valid."""
    if not ANTHROPIC_API_KEY:
        return {"configured": False, "error": "ANTHROPIC_API_KEY not set"}
    
    if not ANTHROPIC_API_KEY.startswith("sk-ant-"):
        return {"configured": False, "error": "Invalid API key format"}
    
    try:
        client = _get_client()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        return {
            "configured": True,
            "model": CLAUDE_MODEL,
            "status": "ok"
        }
    except anthropic.AuthenticationError:
        return {"configured": False, "error": "Invalid API key"}
    except Exception as e:
        return {"configured": False, "error": str(e)}
