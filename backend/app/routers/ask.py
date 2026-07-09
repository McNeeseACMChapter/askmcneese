"""POST /ask — Full RAG pipeline with Claude answer generation.



Pipeline: Question → Web Search OR ChromaDB retrieval → Claude generation → Answer with citations

Supports both regular POST and Server-Sent Events (SSE) streaming.



The system now supports TWO modes:

1. Live Web Search (default): Searches mcneese.edu in real-time

2. Knowledge Base: Uses pre-indexed ChromaDB content



Live search provides more comprehensive coverage for any query.

"""



from __future__ import annotations



import asyncio

import json

import time

from typing import AsyncGenerator



from fastapi import APIRouter, HTTPException

from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field



from app.services.retrieval import search_chunks, get_collection_stats, RetrievedChunk

from app.services.query_logger import (

    create_query_id,

    log_full_query,

    get_pipeline_stats,

    debug_trace_enabled,

)

from app.services.query_expansion import expand_query

from app.services.llm import generate_answer, generate_answer_stream, check_api_key, CLAUDE_MODEL

from app.services.web_search import search_and_fetch, pages_to_context, FetchedPage

from app.services.intent import classify_intent, Intent

from app.services.persona import (

    detect_persona,

    needs_clarification,

    clarification_question,

    already_clarified,

)

from app.services.answer_format import format_chunks_as_answer, _format_web_results



router = APIRouter(prefix="/ask", tags=["ask"])





class AskRequest(BaseModel):

    question: str = Field(..., min_length=1, max_length=1000, description="The user's question")

    stream: bool = Field(default=False, description="Whether to stream the response")

    use_web_search: bool = Field(default=False, description="Use knowledge base by default (False); set True for live web search fallback")

    history: list[dict] | None = Field(

        default=None,

        description="Prior conversation turns as [{role, content}] for persona/context detection",

    )





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

    1. Search for relevant content (web search OR knowledge base)

    2. Fetch and read actual page content

    3. Generate answer using Claude with real context

    4. Return answer with citations (real URLs)

    

    Set stream=true for Server-Sent Events streaming response.

    Set use_web_search=false to use pre-indexed knowledge base instead.

    """

    if body.stream:

        return StreamingResponse(

            ask_stream(body.question, body.use_web_search, body.history),

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

    chunk_responses = []

    sources_found = 0

    kb_chunks: list[RetrievedChunk] = []

    

    # Handle greetings / small talk directly (no web search, no LLM needed)

    intent_result = classify_intent(body.question)

    if intent_result.intent != Intent.QUESTION:

        total_ms = int((time.perf_counter() - start_time) * 1000)

        return AskResponse(

            question=body.question,

            answer=intent_result.reply,

            chunks=[],

            num_results=0,

            query_id=query_id,

            model="conversational",

            tokens_used=0,

            retrieval_ms=0,

            generation_ms=None,

            total_ms=total_ms,

        )



    # Persona-clarification branch: for applicant-category-dependent questions

    # (scholarships, admissions, "how do I apply") where the stage is ambiguous,

    # ask ONE clarifying question instead of a generic everyone-answer.

    if needs_clarification(body.question, body.history) and not already_clarified(body.history):

        total_ms = int((time.perf_counter() - start_time) * 1000)

        return AskResponse(

            question=body.question,

            answer=clarification_question(body.question, body.history),

            chunks=[],

            num_results=0,

            query_id=query_id,

            model="clarification",

            tokens_used=0,

            retrieval_ms=0,

            generation_ms=None,

            total_ms=total_ms,

        )



    persona = detect_persona(body.question, body.history)



    try:

        retrieval_start = time.perf_counter()

        

        if body.use_web_search:

            # LIVE WEB SEARCH MODE

            # Search mcneese.edu and fetch real page content

            fetched_pages = await search_and_fetch(body.question, max_pages=5)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            

            if fetched_pages:

                context, sources = pages_to_context(fetched_pages)

                sources_found = len(fetched_pages)

                

                # Convert to chunk responses for compatibility

                chunk_responses = [

                    ChunkResponse(

                        chunk_id=s["id"],

                        text=s["snippet"],

                        source_url=s["url"],

                        title=s["title"],

                        category="web-search",

                        score=1.0,

                    )

                    for s in sources

                ]

                

                # Generate answer from fetched content

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": page.content, "title": page.title, "source_url": page.url}

                    for page in fetched_pages

                ]

                

                try:

                    result = await asyncio.to_thread(

                        generate_answer,

                        body.question,

                        chunk_dicts,

                        persona=persona,

                    )

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = result.answer

                    model = result.model

                    tokens_used = result.tokens_used

                except Exception as llm_error:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    # Fallback: summarize fetched content

                    answer = _format_web_results(fetched_pages, body.question)

                    model = "fallback-no-llm"

                    tokens_used = 0

            else:

                answer = "I couldn't find relevant information about that on the McNeese website. Please try rephrasing your question or ask about specific topics like admissions, programs, financial aid, or campus services."

                model = None

                tokens_used = None

        else:

            # KNOWLEDGE BASE MODE (original behavior)

            chunks = search_chunks(body.question)

            kb_chunks = chunks

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = len(chunks)

            

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

            

            if chunks:

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": c.text, "title": c.title, "source_url": c.source_url}

                    for c in chunks

                ]

                

                try:

                    result = await asyncio.to_thread(

                        generate_answer,

                        body.question,

                        chunk_dicts,

                        persona=persona,

                    )

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = result.answer

                    model = result.model

                    tokens_used = result.tokens_used

                except Exception:

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    answer = format_chunks_as_answer(chunks, body.question)

                    model = "fallback-no-llm"

                    tokens_used = 0

            else:

                answer = "I couldn't find relevant information in the knowledge base. Try using web search mode for broader coverage."

                model = None

                tokens_used = None

        

        total_ms = int((time.perf_counter() - start_time) * 1000)

        

        # Web pages are FetchedPage objects, not RetrievedChunk; log schema differs.

        log_chunks = [] if body.use_web_search else kb_chunks

        # Debug-trace extras: only computed/passed when the flag is enabled so the

        # default log stays minimal and no extra work runs in normal operation.

        debug_kwargs: dict = {}

        if debug_trace_enabled():

            debug_kwargs = {

                "intent": intent_result.intent.value,

                "persona": persona,

                "expanded_queries": expand_query(body.question),

                "rerank_scores": [round(c.score, 3) for c in chunk_responses],

                "mode": "web_search" if body.use_web_search else "knowledge_base",

            }

        log_full_query(

            query_id=query_id,

            question=body.question,

            chunks=log_chunks,

            retrieval_ms=retrieval_ms,

            generation_ms=generation_ms if sources_found else None,

            answer_model=model,

            answer_tokens=tokens_used,

            final_status="success" if sources_found else "no_results",

            **debug_kwargs,

        )

        

        return AskResponse(

            question=body.question,

            answer=answer,

            chunks=chunk_responses,

            num_results=sources_found,

            query_id=query_id,

            model=model,

            tokens_used=tokens_used,

            retrieval_ms=retrieval_ms,

            generation_ms=generation_ms if sources_found else None,

            total_ms=total_ms,

        )

        

    except Exception as e:

        total_ms = int((time.perf_counter() - start_time) * 1000)

        log_full_query(

            query_id=query_id,

            question=body.question,

            chunks=[],

            retrieval_ms=retrieval_ms,

            final_status="error",

            error_step="pipeline",

            error_message=str(e),

        )

        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")





async def ask_stream(question: str, use_web_search: bool = True,

                     history: list[dict] | None = None) -> AsyncGenerator[str, None]:

    """

    Stream the response using Server-Sent Events.

    

    Events:

    - step: Pipeline step updates (search, fetch, generation)

    - chunk: Text chunks as they're generated

    - citations: Source citations with real URLs

    - done: Final response metadata

    - error: Error information

    """

    query_id = create_query_id()

    start_time = time.perf_counter()

    retrieval_ms = 0

    generation_ms = 0

    sources_found = 0

    

    def send_event(event: str, data: dict) -> str:

        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    

    # Handle greetings / small talk directly (no web search, no LLM needed)

    intent_result = classify_intent(question)

    if intent_result.intent != Intent.QUESTION:

        yield send_event("chunk", {"text": intent_result.reply})

        total_ms = int((time.perf_counter() - start_time) * 1000)

        yield send_event("done", {

            "query_id": query_id,

            "num_results": 0,

            "retrieval_ms": 0,

            "generation_ms": 0,

            "total_ms": total_ms,

            "mode": "conversational",

        })

        return



    # Persona-clarification branch (ask ONE question when stage is ambiguous).

    if needs_clarification(question, history) and not already_clarified(history):

        yield send_event("chunk", {"text": clarification_question(question, history)})

        total_ms = int((time.perf_counter() - start_time) * 1000)

        yield send_event("done", {

            "query_id": query_id,

            "num_results": 0,

            "retrieval_ms": 0,

            "generation_ms": 0,

            "total_ms": total_ms,

            "mode": "clarification",

        })

        return



    persona = detect_persona(question, history)



    try:

        if use_web_search:

            # LIVE WEB SEARCH MODE

            yield send_event("step", {"step": "search", "status": "started", "message": "Searching mcneese.edu..."})

            

            retrieval_start = time.perf_counter()

            fetched_pages = await search_and_fetch(question, max_pages=5)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = len(fetched_pages)

            

            yield send_event("step", {

                "step": "search", 

                "status": "completed", 

                "message": f"Found and read {sources_found} pages",

                "duration_ms": retrieval_ms

            })

            

            # Send citations with real URLs

            citations = [

                {"id": f"src-{i}", "title": p.title, "url": p.url, "snippet": p.content[:200]}

                for i, p in enumerate(fetched_pages, 1)

            ]

            yield send_event("citations", {"citations": citations})

            

            if fetched_pages:

                yield send_event("step", {"step": "generation", "status": "started", "message": "Generating answer from sources..."})

                

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": page.content, "title": page.title, "source_url": page.url}

                    for page in fetched_pages

                ]

                

                try:

                    full_answer = ""

                    async for text_chunk in generate_answer_stream(question, chunk_dicts, persona=persona):

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

                    generation_ms = int((time.perf_counter() - generation_start) * 1000)

                    fallback_answer = _format_web_results(fetched_pages, question)

                    yield send_event("chunk", {"text": fallback_answer})

                    yield send_event("step", {

                        "step": "generation", 

                        "status": "completed", 

                        "message": "Formatted from sources (LLM unavailable)",

                        "duration_ms": generation_ms

                    })

            else:

                yield send_event("chunk", {

                    "text": "I couldn't find relevant information about that on the McNeese website. Please try rephrasing your question or ask about specific topics."

                })

        else:

            # KNOWLEDGE BASE MODE

            yield send_event("step", {"step": "retrieval", "status": "started", "message": "Searching knowledge base..."})

            

            retrieval_start = time.perf_counter()

            chunks = search_chunks(question)

            retrieval_ms = int((time.perf_counter() - retrieval_start) * 1000)

            sources_found = len(chunks)

            

            yield send_event("step", {

                "step": "retrieval", 

                "status": "completed", 

                "message": f"Found {sources_found} relevant sources",

                "duration_ms": retrieval_ms

            })

            

            citations = [

                {"id": c.chunk_id, "title": c.title, "url": c.source_url, "snippet": c.text[:200]}

                for c in chunks

            ]

            yield send_event("citations", {"citations": citations})

            

            if chunks:

                yield send_event("step", {"step": "generation", "status": "started", "message": "Generating answer..."})

                

                generation_start = time.perf_counter()

                chunk_dicts = [

                    {"text": c.text, "title": c.title, "source_url": c.source_url}

                    for c in chunks

                ]

                

                try:

                    full_answer = ""

                    async for text_chunk in generate_answer_stream(question, chunk_dicts, persona=persona):

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

                    "text": "I couldn't find relevant information in the knowledge base. Try enabling web search for broader coverage."

                })

        

        total_ms = int((time.perf_counter() - start_time) * 1000)

        

        debug_kwargs: dict = {}

        if debug_trace_enabled():

            debug_kwargs = {

                "intent": intent_result.intent.value,

                "persona": persona,

                "expanded_queries": expand_query(question),

                "mode": "web_search" if use_web_search else "knowledge_base",

            }

        log_full_query(

            query_id=query_id,

            question=question,

            chunks=[],

            retrieval_ms=retrieval_ms,

            generation_ms=generation_ms if sources_found else None,

            answer_model=CLAUDE_MODEL if sources_found else None,

            final_status="success" if sources_found else "no_results",

            **debug_kwargs,

        )

        

        yield send_event("done", {

            "query_id": query_id,

            "num_results": sources_found,

            "retrieval_ms": retrieval_ms,

            "generation_ms": generation_ms,

            "total_ms": total_ms,

            "mode": "web_search" if use_web_search else "knowledge_base",

        })

        

    except Exception as e:

        yield send_event("error", {"message": str(e)})

        log_full_query(

            query_id=query_id,

            question=question,

            chunks=[],

            retrieval_ms=retrieval_ms,

            final_status="error",

            error_step="stream",

            error_message=str(e),

        )





@router.get("/stats")

async def ask_stats() -> dict:

    """Get statistics about the knowledge base, web search, and pipeline."""

    kb_stats = get_collection_stats()

    pipeline_stats = get_pipeline_stats()

    llm_status = check_api_key()

    

    return {

        "knowledge_base": kb_stats,

        "pipeline": pipeline_stats,

        "llm": llm_status,

        "web_search": {

            "enabled": True,

            "domains": ["mcneese.edu", "catalog.mcneese.edu", "mcneesesports.com"],

            "description": "Live search across McNeese websites",

        },

        "modes": {

            "web_search": "Search and read mcneese.edu pages in real-time (default)",

            "knowledge_base": "Use pre-indexed content from source registry",

        }

    }


