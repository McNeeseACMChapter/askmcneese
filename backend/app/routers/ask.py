"""POST /ask — Full RAG pipeline with Claude answer generation.

Pipeline: Question → ChromaDB retrieval → Claude generation → Answer with citations
Supports both regular POST and Server-Sent Events (SSE) streaming.
"""

from __future__ import annotations

import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.retrieval import search_chunks, get_collection_stats, RetrievedChunk
from app.services.query_logger import create_query_id, log_full_query, get_pipeline_stats
from app.services.llm import generate_answer, generate_answer_stream, check_api_key


def format_chunks_as_answer(chunks: list[RetrievedChunk], question: str = "") -> str:
    """
    Format chunks as a readable answer when LLM is unavailable.
    Extracts the most relevant sections instead of dumping raw text.
    """
    if not chunks:
        return "No relevant information found."
    
    question_lower = question.lower()
    
    # Extract key terms from question
    stopwords = {"what", "when", "where", "which", "that", "this", "have", "does", "about", "from", "the", "is", "are"}
    key_terms = [w.strip("?.,!") for w in question_lower.split() if len(w) > 2 and w not in stopwords]
    
    # Boilerplate phrases to skip
    skip_phrases = [
        'cookie policy', 'privacy statement', 'skip to content', 
        'learn more', 'no thanks', 'i agree', 'expand\nexpand',
        'close menu', 'website terms', 'by using our site',
        'equal opportunity', 'compliance', 'reasonable accommodations',
        'university operates', 'treatment or employment', 'fax at',
        'reserves the right to change', 'catalog is not'
    ]
    
    best_sections = []
    seen = set()
    
    for chunk in chunks:
        text = chunk.text.strip()
        
        # Split by markdown headers (##, ###)
        import re
        sections = re.split(r'\n(?=##?\s)', text)
        
        for section in sections:
            section = section.strip()
            if len(section) < 15:
                continue
            
            section_lower = section.lower()
            
            # Skip boilerplate
            if any(p in section_lower for p in skip_phrases):
                continue
            
            # Calculate relevance score
            score = 0
            
            # Keyword matches
            for term in key_terms:
                if term in section_lower:
                    score += 2
            
            # High-value patterns (actual content, not navigation)
            high_value = ['deadline', 'august', 'december', 'may', 'january', 'february',
                         'requirement', 'gpa', 'sat', 'act', 'tuition', 'cost', 'fee',
                         'scholarship', 'financial aid', 'fafsa', 'apply', 'admission']
            for hv in high_value:
                if hv in section_lower:
                    score += 3
            
            # Penalize navigation-looking content
            nav_indicators = ['expand', 'overview', 'next step', 'explore this section',
                             'visit mcneese', 'apply as', 'i am a']
            for nav in nav_indicators:
                if nav in section_lower:
                    score -= 1
            
            # Check for actual data (numbers, dates)
            if re.search(r'\b\d{1,2}\b', section):  # Has numbers (like dates)
                score += 2
            
            # Deduplicate
            key = section[:80]
            if key in seen:
                continue
            seen.add(key)
            
            if score > 2:
                best_sections.append((score, section, chunk.title, chunk.source_url))
    
    # Sort by score and take best
    best_sections.sort(key=lambda x: -x[0])
    
    # If the best section is significantly better, just show that one
    if best_sections and best_sections[0][0] >= 8:
        top = [best_sections[0]]
    elif best_sections:
        # Only include if score is high enough
        top = [s for s in best_sections if s[0] >= 6][:1]
        if not top and best_sections[0][0] >= 4:
            top = [best_sections[0]]
    else:
        top = []
    
    if not top:
        # Fallback: show beginning of first chunk (cleaned)
        chunk = chunks[0]
        text = chunk.text
        # Remove cookie/header noise
        for phrase in skip_phrases:
            text = text.replace(phrase, '')
        lines = [l for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
        clean = '\n'.join(lines[:8])
        return f"{clean[:400]}...\n\n📚 Source: [{chunk.title}]({chunk.source_url})"
    
    # Build the answer
    parts = []
    for score, section, title, url in top:
        # Clean up
        clean = section.replace('\n\n\n', '\n\n').strip()
        if len(clean) > 350:
            clean = clean[:350] + "..."
        parts.append(clean)
    
    # Get unique sources
    sources = list(dict.fromkeys((s[2], s[3]) for s in top))
    source_text = ', '.join(f"[{t}]({u})" for t, u in sources)
    
    return '\n\n'.join(parts) + f"\n\n📚 Source: {source_text}"

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="The user's question")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    source_url: str
    title: str
    category: str
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    chunks: list[ChunkResponse]
    num_results: int
    query_id: str
    model: str | None = None
    tokens_used: int | None = None
    retrieval_ms: int
    generation_ms: int | None = None
    total_ms: int


@router.post("")
async def ask(body: AskRequest):
    """
    Ask a question and get an AI-generated answer from McNeese sources.
    
    Pipeline steps:
    1. Search ChromaDB for relevant chunks
    2. Generate answer using Claude with retrieved context
    3. Return answer with citations
    
    Set stream=true for Server-Sent Events streaming response.
    """
    if body.stream:
        return StreamingResponse(
            ask_stream(body.question),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    query_id = create_query_id()
    start_time = time.perf_counter()
    retrieval_ms = 0
    generation_ms = 0
    chunks = []
    
    try:
        # Step 1: Retrieval
        retrieval_start = time.perf_counter()
        chunks = search_chunks(body.question)
        retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)
        
        chunk_responses = [
            ChunkResponse(
                chunk_id=c.chunk_id,
                text=c.text,
                source_url=c.source_url,
                title=c.title,
                category=c.category,
                score=c.score,
            )
            for c in chunks
        ]
        
        # Step 2: Generation (with fallback if LLM unavailable)
        if chunks:
            generation_start = time.perf_counter()
            chunk_dicts = [
                {"text": c.text, "title": c.title, "source_url": c.source_url}
                for c in chunks
            ]
            
            try:
                result = generate_answer(body.question, chunk_dicts)
                generation_ms = int((time.perf_counter() - generation_start) * 1000)
                answer = result.answer
                model = result.model
                tokens_used = result.tokens_used
            except Exception as llm_error:
                # Fallback: extract relevant sections without LLM
                generation_ms = int((time.perf_counter() - generation_start) * 1000)
                answer = format_chunks_as_answer(chunks, body.question)
                model = "fallback-no-llm"
                tokens_used = 0
        else:
            answer = "I couldn't find relevant information about that in the McNeese knowledge base. Try rephrasing your question or ask about admissions, academics, or campus life."
            model = None
            tokens_used = None
        
        total_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log the query
        log_full_query(
            query_id=query_id,
            question=body.question,
            chunks=chunks,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms if chunks else None,
            answer_model=model,
            answer_tokens=tokens_used,
            final_status="success" if chunks else "no_results",
        )
        
        return AskResponse(
            question=body.question,
            answer=answer,
            chunks=chunk_responses,
            num_results=len(chunks),
            query_id=query_id,
            model=model,
            tokens_used=tokens_used,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms if chunks else None,
            total_ms=total_ms,
        )
        
    except Exception as e:
        total_ms = int((time.perf_counter() - start_time) * 1000)
        log_full_query(
            query_id=query_id,
            question=body.question,
            chunks=chunks,
            retrieval_ms=retrieval_ms,
            final_status="error",
            error_step="generation" if chunks else "retrieval",
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


async def ask_stream(question: str) -> AsyncGenerator[str, None]:
    """
    Stream the response using Server-Sent Events.
    
    Events:
    - step: Pipeline step updates (retrieval, generation)
    - chunk: Text chunks as they're generated
    - citations: Source citations
    - done: Final response metadata
    - error: Error information
    """
    query_id = create_query_id()
    start_time = time.perf_counter()
    retrieval_ms = 0
    generation_ms = 0
    chunks = []
    
    def send_event(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
    
    try:
        # Step 1: Retrieval
        yield send_event("step", {"step": "retrieval", "status": "started", "message": "Searching knowledge base..."})
        
        retrieval_start = time.perf_counter()
        chunks = search_chunks(question)
        retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)
        
        yield send_event("step", {
            "step": "retrieval", 
            "status": "completed", 
            "message": f"Found {len(chunks)} relevant sources",
            "duration_ms": retrieval_ms
        })
        
        # Send citations
        citations = [
            {"id": c.chunk_id, "title": c.title, "url": c.source_url, "snippet": c.text[:200]}
            for c in chunks
        ]
        yield send_event("citations", {"citations": citations})
        
        # Step 2: Generation (with fallback)
        if chunks:
            yield send_event("step", {"step": "generation", "status": "started", "message": "Generating answer..."})
            
            generation_start = time.perf_counter()
            chunk_dicts = [
                {"text": c.text, "title": c.title, "source_url": c.source_url}
                for c in chunks
            ]
            
            try:
                # Stream the answer
                full_answer = ""
                async for text_chunk in generate_answer_stream(question, chunk_dicts):
                    full_answer += text_chunk
                    yield send_event("chunk", {"text": text_chunk})
                
                generation_ms = int((time.perf_counter() - generation_start) * 1000)
                
                yield send_event("step", {
                    "step": "generation", 
                    "status": "completed", 
                    "message": "Answer generated",
                    "duration_ms": generation_ms
                })
            except Exception:
                # Fallback: extract relevant sections
                generation_ms = int((time.perf_counter() - generation_start) * 1000)
                fallback_answer = format_chunks_as_answer(chunks, question)
                yield send_event("chunk", {"text": fallback_answer})
                yield send_event("step", {
                    "step": "generation", 
                    "status": "completed", 
                    "message": "Formatted from sources (LLM unavailable)",
                    "duration_ms": generation_ms
                })
        else:
            yield send_event("chunk", {
                "text": "I couldn't find relevant information about that in the McNeese knowledge base. Try rephrasing your question or ask about admissions, academics, or campus life."
            })
        
        total_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log the query
        log_full_query(
            query_id=query_id,
            question=question,
            chunks=chunks,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms if chunks else None,
            answer_model="claude-sonnet-4-20250514" if chunks else None,
            final_status="success" if chunks else "no_results",
        )
        
        # Send done event
        yield send_event("done", {
            "query_id": query_id,
            "num_results": len(chunks),
            "retrieval_ms": retrieval_ms,
            "generation_ms": generation_ms,
            "total_ms": total_ms,
        })
        
    except Exception as e:
        yield send_event("error", {"message": str(e)})
        log_full_query(
            query_id=query_id,
            question=question,
            chunks=chunks,
            retrieval_ms=retrieval_ms,
            final_status="error",
            error_step="stream",
            error_message=str(e),
        )


@router.get("/stats")
async def ask_stats() -> dict:
    """Get statistics about the knowledge base and pipeline."""
    kb_stats = get_collection_stats()
    pipeline_stats = get_pipeline_stats()
    llm_status = check_api_key()
    
    return {
        "knowledge_base": kb_stats,
        "pipeline": pipeline_stats,
        "llm": llm_status,
    }
