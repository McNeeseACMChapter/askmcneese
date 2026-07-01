# Sprint 3 — Micro-Step Task Breakdown

**Sprint:** June 30 – July 7, 2026  
**Owner:** PM (Prince Pudasaini)  
**Last Updated:** June 30, 2026 @ 8:03 PM

---

## Progress Summary

| Task | Status | PR |
|------|--------|-----|
| S3-01 | ✅ COMPLETE | #14 |
| S3-02 | ✅ COMPLETE | #14 merged |
| S3-03 | ⏭️ SUPERSEDED | PM's PR #15 includes this |
| S3-04 | ✅ COMPLETE | #15 |
| S3-05 | ✅ COMPLETE | #15 merged |
| S3-06 | 🔄 IN PROGRESS | — |
| S3-07 | 🔄 IN PROGRESS | — |
| S3-08 | ⬜ PENDING | — |

---

## S3-01: Commit and Push Backend Work ✅ COMPLETE

**Status:** ✅ DONE — PR #14 merged  
**Completed:** June 30, 2026

### Steps:

1. **Verify backend files are correct**
   ```bash
   cd backend
   ls app/routers/      # Should have ask.py, health.py
   ls app/services/     # Should have retrieval.py, llm.py, query_logger.py, __init__.py
   ```

2. **Check main.py includes ask router**
   ```python
   # In backend/app/main.py, verify:
   from app.routers import health, ask
   app.include_router(ask.router)
   ```

3. **Update .env.example with new variables**
   ```env
   ANTHROPIC_API_KEY=your-api-key-here
   CLAUDE_MODEL=claude-sonnet-4-20250514
   CLAUDE_MAX_TOKENS=1024
   ```

4. **Stage backend changes**
   ```bash
   git add backend/app/routers/ask.py
   git add backend/app/services/
   git add backend/requirements.txt
   git add backend/app/main.py
   git add .env.example
   ```

5. **Commit with descriptive message**
   ```bash
   git commit -m "BE-06/07: Add /ask endpoint with full RAG pipeline

   - POST /ask with retrieval + Claude generation
   - SSE streaming support for real-time responses
   - Query logging to JSONL
   - Fallback when LLM unavailable
   - /ask/stats endpoint for pipeline statistics"
   ```

6. **Push to feature branch**
   ```bash
   git checkout -b feature/backend-ask
   git push -u origin feature/backend-ask
   ```

---

## S3-02: Create PR for Backend `/ask` Endpoint ✅ COMPLETE

**Status:** ✅ DONE — PR #14 merged to dev  
**Completed:** June 30, 2026  
**URL:** https://github.com/McNeeseACMChapter/askmcneese/pull/14

### Steps:

1. **Go to GitHub repo**
   - URL: https://github.com/McNeeseACMChapter/askmcneese

2. **Click "Compare & pull request"** for `feature/backend-ask`

3. **Write PR description**
   ```markdown
   ## Summary
   - Implements BE-06: `POST /ask` endpoint with ChromaDB retrieval
   - Implements BE-07: Query logging to JSONL
   - BONUS: Claude LLM integration with streaming

   ## Changes
   - `backend/app/routers/ask.py` — Full RAG pipeline
   - `backend/app/services/retrieval.py` — ChromaDB search
   - `backend/app/services/llm.py` — Claude integration
   - `backend/app/services/query_logger.py` — Logging service
   - Updated `requirements.txt` with anthropic SDK

   ## Test Plan
   - [ ] Backend starts without errors
   - [ ] `POST /ask` returns retrieved chunks
   - [ ] Streaming works with `stream: true`
   - [ ] Query logs appear in `backend/logs/query_logs.jsonl`
   ```

4. **Request review** (self-review if needed)

5. **Merge to dev** after CI passes

---

## S3-03: Merge Evan's FE-06 Branch ⏭️ SUPERSEDED

**Status:** ⏭️ SUPERSEDED — PM's PR #15 includes and extends FE-06 functionality  
**Note:** Evan's branch `frontend-code/evan-weber` remains as reference but PM's complete implementation was merged instead.

### Original Steps:

1. **Verify BE-06 is merged to dev**
   ```bash
   git checkout dev
   git pull origin dev
   # Confirm ask.py exists
   ls backend/app/routers/ask.py
   ```

2. **Create PR for Evan's branch** (if not already exists)
   ```bash
   gh pr create --base dev --head frontend-code/evan-weber \
     --title "FE-06: Wire /ask hook and render retrieved citations" \
     --body "Evan Weber's Sprint 2 frontend work. Depends on BE-06."
   ```

3. **Review Evan's changes**
   - Check `useAsk.ts` hook
   - Check `MessageBubble.tsx` citation rendering
   - Check types match backend response

4. **Fix any merge conflicts** (if Evan's types differ from PM's enhanced types)

5. **Merge to dev**

---

## S3-04: Commit and Push Frontend Work ✅ COMPLETE

**Status:** ✅ DONE — Committed as `87959a6`  
**Completed:** June 30, 2026

### Steps:

1. **Create feature branch**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/frontend-ui-refactor
   ```

2. **Stage new component files**
   ```bash
   git add frontend/src/components/chat/
   git add frontend/src/components/layout/
   git add frontend/src/components/ui/
   git add frontend/src/components/feedback/
   ```

3. **Stage new hooks and lib**
   ```bash
   git add frontend/src/hooks/useAsk.ts
   git add frontend/src/hooks/useConversations.ts
   git add frontend/src/lib/
   ```

4. **Stage styles**
   ```bash
   git add frontend/src/styles/
   git add frontend/src/index.css
   git add frontend/tailwind.config.js
   ```

5. **Stage modified files**
   ```bash
   git add frontend/src/App.tsx
   git add frontend/src/types.ts
   git add frontend/package.json
   git add frontend/package-lock.json
   ```

6. **Remove deleted files from tracking**
   ```bash
   git rm frontend/src/components/ChatInput.tsx
   git rm frontend/src/components/EmptyState.tsx
   git rm frontend/src/components/MessageBubble.tsx
   git rm frontend/src/components/StatusBadge.tsx
   git rm frontend/src/data/sampleMessages.ts
   ```

7. **Commit**
   ```bash
   git commit -m "Frontend UI refactor: Design system + conversations + animations

   - New component architecture (chat/, layout/, ui/, feedback/)
   - CSS variables for design tokens (colors, shadows, radii)
   - Framer Motion animations throughout
   - Conversation history with localStorage
   - Splash screen with McNeese branding
   - SSE streaming in useAsk hook
   - Responsive sidebar navigation"
   ```

8. **Push**
   ```bash
   git push -u origin feature/frontend-ui-refactor
   ```

---

## S3-05: Create PR for Frontend UI Refactor ✅ COMPLETE

**Status:** ✅ DONE — PR #15 merged to dev  
**Completed:** June 30, 2026  
**URL:** https://github.com/McNeeseACMChapter/askmcneese/pull/15

### Steps:

1. **Create PR on GitHub**

2. **Write PR description**
   ```markdown
   ## Summary
   Complete frontend refactor with production-ready UI

   ## New Features
   - Splash screen with animated branding
   - Sidebar with conversation history
   - Citation cards for source display
   - Pipeline status indicators during /ask
   - Dark mode CSS variables (ready for toggle)

   ## Technical Changes
   - Design system in `styles/variables.css`
   - Tailwind config extended with brand colors
   - Framer Motion variants in `lib/motion.ts`
   - Type-safe streaming in `useAsk.ts`

   ## Test Plan
   - [ ] App loads with splash screen
   - [ ] Questions send to /ask endpoint
   - [ ] Citations display in bubbles
   - [ ] Conversation history persists
   - [ ] Mobile sidebar works
   ```

3. **Merge to dev** after review

---

## S3-06: Integration Testing

**Priority:** MEDIUM  
**Estimated time:** 1 hour

### Steps:

1. **Pull merged dev**
   ```bash
   git checkout dev
   git pull origin dev
   ```

2. **Start backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Verify ChromaDB has data**
   ```bash
   cd ../crawler
   python ingest.py --url https://catalog.mcneese.edu/
   ```

4. **Start frontend**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

5. **Test scenarios**
   - [ ] Health badge shows "Online"
   - [ ] Ask "What are the admission deadlines?"
   - [ ] Verify citations appear
   - [ ] Check query logged to JSONL
   - [ ] Test streaming mode
   - [ ] Test conversation persistence
   - [ ] Test mobile responsive

6. **Document any issues** in `docs/qa/sprint3_issues.md`

---

## S3-07: Update Documentation

**Priority:** MEDIUM  
**Estimated time:** 30 minutes

### Steps:

1. **Update `docs/setup.md`** with:
   - ANTHROPIC_API_KEY setup
   - CLAUDE_MODEL configuration
   - Query logging location

2. **Update `README.md`** with:
   - New feature list
   - Updated screenshots
   - Architecture diagram update

3. **Update `.env.example`** with all new variables

4. **Create `docs/api.md`** documenting:
   - `POST /ask` endpoint
   - `GET /ask/stats` endpoint
   - SSE event format

---

## S3-08: Prepare Sprint 4 Plan

**Priority:** MEDIUM  
**Estimated time:** 30 minutes

### Steps:

1. **Review what's still pending**
   - BE-08: Expand ingest to more sources
   - Production deployment
   - Admin dashboard
   - User feedback system

2. **Draft Sprint 4 tickets**
   - S4-01: Expand crawler to 15+ sources
   - S4-02: Add feedback thumbs up/down
   - S4-03: Admin stats dashboard
   - S4-04: Deployment to cloud

3. **Create `docs/pm/sprint4/README.md`** with plan

4. **Prepare for Thursday meeting** (July 3rd)

---

## Checklist Summary

| Task | Status | Notes |
|------|--------|-------|
| S3-01: Commit backend | ✅ DONE | PR #14 |
| S3-02: PR for backend | ✅ DONE | Merged to dev |
| S3-03: Merge Evan's FE-06 | ⏭️ SUPERSEDED | PM's PR covers this |
| S3-04: Commit frontend | ✅ DONE | PR #15 |
| S3-05: PR for frontend | ✅ DONE | Merged to dev |
| S3-06: Integration testing | 🔄 IN PROGRESS | Testing locally |
| S3-07: Update docs | 🔄 IN PROGRESS | Sprint 3 docs updated |
| S3-08: Sprint 4 plan | ⬜ PENDING | For Thursday meeting |

---

**Sprint 3 Progress: 62.5% complete (5/8 tasks)**

*Remaining tasks (S3-06, S3-07, S3-08) in progress for Thursday meeting.*
