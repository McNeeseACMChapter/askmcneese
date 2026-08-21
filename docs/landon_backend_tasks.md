# Backend Tasks for Landon — Sprint 2

**Date:** June 30, 2026  
**From:** Prince (PM)  
**Priority:** Urgent

---

Hey Landon,

Hope you're doing well. I need to be straight with you — we're behind on the backend work for Sprint 2 and Evan is waiting on you. Here's where we stand:

## Current Situation

- **Evan completed FE-06** on June 25 (5 days ago)
- His frontend code calls `POST /ask` but that endpoint **doesn't exist yet**
- His branch `frontend-code/evan-weber` can't be merged until the backend is ready
- Sprint 2 was supposed to be done by now

## What You Need to Deliver

### 1. BE-06: `POST /ask` Endpoint (HIGH PRIORITY)

Create `backend/app/routers/ask.py` that:

```
POST /ask
Request:  { "question": "string" }
Response: { 
  "query_id": "string",
  "question_text": "string", 
  "chunks": [...],
  "num_results": int,
  "latency_ms": int 
}
```

**Requirements:**
- Read from the existing ChromaDB collection (`crawler/chroma_db`)
- Use the same collection name: `askmcneese_sources`
- Return top 3-5 relevant chunks using semantic search
- Each chunk needs: `chunk_id`, `text`, `source_url`, `title`, `category`, `trust_tier`
- Register the router in `backend/app/main.py`

**Evan's frontend expects this exact response format** — check `frontend/src/types.ts` on his branch.

### 2. BE-07: Query Logging

Log each query to `logs/query_logs.jsonl` with:
- `query_id`
- `timestamp`
- `question`
- `num_results`
- `latency_ms`

### 3. BE-08: Expand Ingest (Lower Priority)

Run `crawler/ingest.py` on more Approved sources from `knowledge/source_registry_seed.csv`.

---

## Reference Code

The crawler pipeline is already done and working on `dev`. Look at:
- `crawler/ingest.py` — How chunks get into ChromaDB
- `crawler/chunker.py` — Chunk format and metadata
- `backend/app/routers/health.py` — Example router structure

**Use FastAPI, not Django.** The whole project is FastAPI.

## Environment Setup

```bash
# 1. Pull latest dev
git checkout dev
git pull origin dev

# 2. Install backend deps
cd backend
pip install -r requirements.txt

# 3. Make sure ChromaDB has data
cd ../crawler
python ingest.py --url https://catalog.mcneese.edu/

# 4. Run backend
cd ../backend
uvicorn app.main:app --reload
```

## Your Branch

Create: `feature/backend-ask`

When done, open a PR to `dev` and tag me for review.

---

## Timeline

Evan has been waiting 5 days. I need BE-06 done ASAP so we can:
1. Merge Evan's frontend work
2. Have a working end-to-end flow
3. Move to Sprint 3

**Please reply with your availability and when you can have BE-06 ready.**

If you're stuck on anything, reach out. I'd rather help you unblock than have this drag on longer.

— Prince
