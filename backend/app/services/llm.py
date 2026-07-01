"""Claude LLM answer generation service.

Uses retrieved chunks to generate a coherent answer with citations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import AsyncGenerator

import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))

SYSTEM_PROMPT = """You are AskMcNeese, a helpful AI assistant for McNeese State University.

Your role is to answer questions about McNeese using ONLY the provided source documents.

Guidelines:
1. Answer based ONLY on the provided sources - never make up information
2. Be friendly and helpful - you're helping prospective and current students
3. Use a conversational but professional tone
4. If the sources don't contain enough information, say so honestly
5. Keep answers concise but complete (2-4 paragraphs max)
6. Reference sources naturally (e.g., "According to the admissions page...")
7. For dates/deadlines, always note they should verify on the official site

If asked about something not covered in the sources, say:
"I don't have specific information about that in my current knowledge base. I recommend checking the official McNeese website or contacting the relevant department directly."

Never:
- Make up facts, dates, or requirements
- Give advice on matters requiring professional judgment
- Pretend to have information you don't have"""


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


def generate_answer(question: str, chunks: list[dict]) -> GenerationResult:
    """
    Generate an answer using Claude based on retrieved chunks.
    
    Args:
        question: The user's question
        chunks: List of retrieved chunk dicts with text, title, source_url
    
    Returns:
        GenerationResult with the answer and metadata
    """
    client = _get_client()
    
    context = _build_context(chunks)
    
    user_message = f"""Based on the following McNeese sources, answer this question:

Question: {question}

Sources:
{context}

Provide a helpful, accurate answer based only on the sources above."""

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
    chunks: list[dict]
) -> AsyncGenerator[str, None]:
    """
    Stream an answer using Claude based on retrieved chunks.
    
    Yields chunks of text as they're generated.
    """
    client = _get_client()
    
    context = _build_context(chunks)
    
    user_message = f"""Based on the following McNeese sources, answer this question:

Question: {question}

Sources:
{context}

Provide a helpful, accurate answer based only on the sources above."""

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
