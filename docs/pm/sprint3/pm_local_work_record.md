# PM Local Work Record — Sprint 2/3

**Author:** Prince Pudasaini (PM)  
**Date:** June 30, 2026  
**Status:** ✅ PUSHED AND MERGED

---

## Summary

Due to Landon's non-delivery of Backend work, PM completed the full RAG pipeline implementation. This work has been pushed and merged to `dev`:

| PR | Title | Status |
|----|-------|--------|
| #14 | BE-06/BE-07: POST /ask endpoint with full RAG pipeline | ✅ MERGED |
| #15 | FE-06+: Frontend UI refactor with design system | ✅ MERGED |

---

## Backend Work Completed (BE-06, BE-07 + Beyond)

### 1. `/ask` Endpoint (`backend/app/routers/ask.py`)

**Features implemented:**
- Full RAG pipeline: Question → Retrieval → LLM Generation → Response
- Dual response modes:
  - Standard POST: Returns complete `AskResponse`
  - SSE Streaming: Real-time text via Server-Sent Events
- Graceful fallback when LLM unavailable
- Smart section extraction (filters boilerplate/cookie text)
- Pipeline statistics (retrieval_ms, generation_ms, total_ms)
- `/ask/stats` endpoint for knowledge base statistics

**Request/Response:**
```json
// POST /ask
Request:  { "question": "string", "stream": false }
Response: {
  "question": "string",
  "answer": "string",
  "chunks": [...],
  "num_results": int,
  "query_id": "string",
  "model": "string",
  "tokens_used": int,
  "retrieval_ms": int,
  "generation_ms": int,
  "total_ms": int
}
```

### 2. Retrieval Service (`backend/app/services/retrieval.py`)

**Features:**
- ChromaDB semantic search
- Hybrid ranking: 60% embedding similarity + 40% keyword match
- Query expansion for common terms (deadlines, admissions, financial aid)
- Configurable `RETRIEVAL_TOP_K` (default: 3)
- Collection statistics endpoint

**Key functions:**
- `search_chunks(question, top_k)` → `list[RetrievedChunk]`
- `get_collection_stats()` → `dict`
- `_extract_keywords(question)` → `list[str]`
- `_keyword_score(text, keywords)` → `float`

### 3. LLM Service (`backend/app/services/llm.py`)

**Features:**
- Claude Sonnet 4 integration via Anthropic SDK
- Custom system prompt for McNeese context
- Streaming support for real-time responses
- API key validation endpoint

**Key functions:**
- `generate_answer(question, chunks)` → `GenerationResult`
- `generate_answer_stream(question, chunks)` → `AsyncGenerator[str]`
- `check_api_key()` → `dict`

**System prompt:** Instructs Claude to:
- Answer ONLY from provided sources
- Be helpful and conversational
- Reference sources naturally
- Admit when information isn't available

### 4. Query Logger (`backend/app/services/query_logger.py`)

**Features:**
- JSONL logging to `backend/logs/query_logs.jsonl`
- Full pipeline tracking (retrieval → generation → complete)
- Query analytics endpoints

**Logged fields:**
- `query_id`, `timestamp`, `question_text`
- `pipeline_steps` (with timing)
- `retrieved_chunk_ids`, `top_source_urls`
- `num_results`, `answer_generated`, `answer_model`
- `total_latency_ms`, `final_status`

### 5. Environment Variables Added

```env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=1024
CHROMA_DB_PATH=crawler/chroma_db
CHROMA_COLLECTION=askmcneese_sources
RETRIEVAL_TOP_K=3
QUERY_LOG_PATH=backend/logs/query_logs.jsonl
```

---

## Frontend Work Completed (Beyond FE-06)

### 1. Complete UI Refactor

**New component architecture:**
```
frontend/src/
├── components/
│   ├── chat/
│   │   ├── ChatPage.tsx      # Main chat container
│   │   ├── ChatBubble.tsx    # Message bubble with citations
│   │   ├── ChatInput.tsx     # Input with send button
│   │   ├── EmptyState.tsx    # Welcome state with suggestions
│   │   ├── CitationCard.tsx  # Source citation display
│   │   ├── SuggestionPill.tsx # Quick question buttons
│   │   └── TypingIndicator.tsx # Loading state
│   ├── layout/
│   │   ├── Header.tsx        # Top bar with status
│   │   └── Sidebar.tsx       # Conversation history
│   ├── ui/
│   │   ├── Button.tsx        # Reusable button
│   │   └── Badge.tsx         # Status badge
│   └── feedback/
│       ├── SplashScreen.tsx  # Animated intro
│       └── Skeleton.tsx      # Loading placeholder
├── hooks/
│   ├── useAsk.ts             # /ask API with SSE streaming
│   ├── useConversations.ts   # Conversation state management
│   └── useHealth.ts          # Health check polling
├── lib/
│   └── motion.ts             # Framer Motion variants
└── styles/
    └── variables.css         # CSS custom properties
```

### 2. Design System Implementation

**CSS Variables (`styles/variables.css`):**
- Brand colors: McNeese Blue (#00549F), McNeese Gold (#F2A900)
- Surface/background colors
- Text colors (primary, secondary, muted)
- Status colors (success, warning, error)
- Shadows (sm, md, lg)
- Border radius tokens
- Animation durations
- Dark mode support

**Tailwind Extensions (`tailwind.config.js`):**
- Custom colors mapped to CSS variables
- `mcneese-blue`, `mcneese-gold` color utilities
- Custom shadows: `shadow-soft`, `shadow-card`, `shadow-float`
- Custom border radius: `rounded-bubble`
- Animation: `dot-bounce` for typing indicator
- Max widths: `max-w-chat`, `max-w-message`

### 3. Motion System (`lib/motion.ts`)

**Framer Motion variants:**
- `fadeIn`, `slideUp`, `slideInRight`, `slideInLeft`
- `scaleIn` for modals/cards
- `sidebarVariants` for drawer animation
- `overlayVariants` for backdrop
- `staggerContainer`, `listItem` for lists
- `buttonHover`, `buttonTap` micro-interactions

### 4. Splash Screen (`SplashScreen.tsx`)

**Features:**
- Animated background particles
- Logo icon with spring animation
- Letter-by-letter brand name reveal
- Loading progress bar
- McNeese ACM attribution

### 5. Conversation Management (`useConversations.ts`)

**Features:**
- localStorage persistence
- Create/update/delete conversations
- Active conversation selection
- Auto-generated titles from first message
- Date grouping (Today, Yesterday, Previous 7 Days, Older)

### 6. useAsk Hook Enhancements

**Features:**
- SSE streaming support
- Pipeline status tracking
- Abort controller for cancellation
- Error handling with user-friendly messages
- Loading states: `idle`, `connecting`, `searching`, `generating`, `complete`, `error`

---

## Files Changed Summary

### Backend (Untracked/Modified)
| File | Status | Lines |
|------|--------|-------|
| `backend/app/routers/ask.py` | NEW | ~416 |
| `backend/app/services/retrieval.py` | NEW | ~180 |
| `backend/app/services/llm.py` | NEW | ~174 |
| `backend/app/services/query_logger.py` | NEW | ~184 |
| `backend/app/services/__init__.py` | NEW | 0 |
| `backend/app/main.py` | MODIFIED | +router |
| `backend/requirements.txt` | MODIFIED | +anthropic |
| `backend/logs/query_logs.jsonl` | NEW | (runtime) |

### Frontend (Untracked/Modified)
| File | Status | Lines |
|------|--------|-------|
| `frontend/src/App.tsx` | MODIFIED | ~179 |
| `frontend/src/types.ts` | MODIFIED | ~61 |
| `frontend/src/index.css` | MODIFIED | ~45 |
| `frontend/tailwind.config.js` | MODIFIED | ~61 |
| `frontend/src/styles/variables.css` | NEW | ~73 |
| `frontend/src/lib/motion.ts` | NEW | ~111 |
| `frontend/src/hooks/useAsk.ts` | NEW | ~307 |
| `frontend/src/hooks/useConversations.ts` | NEW | ~100+ |
| `frontend/src/components/chat/*.tsx` | NEW | 7 files |
| `frontend/src/components/layout/*.tsx` | NEW | 2 files |
| `frontend/src/components/ui/*.tsx` | NEW | 2 files |
| `frontend/src/components/feedback/*.tsx` | NEW | 2 files |

### Deleted (Sprint 1 components replaced)
- `frontend/src/components/ChatInput.tsx`
- `frontend/src/components/EmptyState.tsx`
- `frontend/src/components/MessageBubble.tsx`
- `frontend/src/components/StatusBadge.tsx`
- `frontend/src/data/sampleMessages.ts`

---

## Dependencies Added

### Backend (`requirements.txt`)
```
anthropic>=0.30.0
```

### Frontend (`package.json`)
```json
"framer-motion": "^11.x"
```

---

## Why This Work Was Done by PM

1. Landon did not deliver BE-06, BE-07, BE-08 in 15 days
2. Evan's FE-06 was blocked waiting for backend
3. PM built the backend to unblock the project
4. PM also enhanced the frontend beyond original scope
5. Project cannot wait indefinitely for one developer

---

## Git History

**Backend commit:** `3558fb8` — "BE-06/BE-07: POST /ask endpoint with full RAG pipeline"  
**Frontend commit:** `87959a6` — "FE-06+: Frontend UI refactor with design system and /ask integration"

**PRs:**
- PR #14: https://github.com/McNeeseACMChapter/askmcneese/pull/14 (merged)
- PR #15: https://github.com/McNeeseACMChapter/askmcneese/pull/15 (merged)

---

*This record documents all work completed by PM for Sprint 2.*
*All work has been pushed and merged to `dev` as of June 30, 2026.*
