# Sprint 3 — Task Assignments

**Sprint:** June 30 – July 7, 2026  
**Meeting:** Thursday, July 3rd, 1-3 PM @ Drew Hall  
**Last Updated:** June 30, 2026

---

## What Was Done (Sprint 2 Completion)

- PR #14: Backend `/ask` endpoint ✅ MERGED
- PR #15: Frontend UI refactor ✅ MERGED

---

## Sprint 3 Work To Be Done

### Summary by Role

| Role | Tasks | Points |
|------|-------|--------|
| **PM** | 5 tasks | 50 pts |
| **Frontend (Evan)** | 4 tasks | 40 pts |
| **Backend** | 4 tasks | 40 pts |
| **Total** | 13 tasks | 130 pts |

---

## PM Tasks (Prince)

### PM-S3-01: Expand Crawler to 5 More Approved Sources
**Points:** 15  
**Due:** July 3

**Steps:**
1. Review `knowledge/source_registry_seed.csv` for Approved URLs
2. Run ingest on 5 new sources:
   ```bash
   cd crawler
   python ingest.py --url https://www.mcneese.edu/admissions/
   python ingest.py --url https://www.mcneese.edu/financial-aid/
   python ingest.py --url https://www.mcneese.edu/academics/
   python ingest.py --url https://www.mcneese.edu/student-life/
   python ingest.py --url https://www.mcneese.edu/about/
   ```
3. Verify chunks in ChromaDB: `GET /ask/stats`
4. Update source_registry_seed.csv with `last_checked_date`

**Deliverable:** 5 new sources ingested, 50+ new chunks

---

### PM-S3-02: Write API Documentation
**Points:** 10  
**Due:** July 2

**Steps:**
1. Create `docs/api.md`
2. Document endpoints:
   - `GET /health` — request/response
   - `POST /ask` — request/response/streaming
   - `GET /ask/stats` — response format
3. Include example curl commands
4. Document SSE event types

**Deliverable:** `docs/api.md` complete

---

### PM-S3-03: Update Setup Guide
**Points:** 10  
**Due:** July 2

**Steps:**
1. Update `docs/setup.md` with:
   - Claude API key setup instructions
   - How to get ANTHROPIC_API_KEY
   - Environment variable reference
2. Add troubleshooting section
3. Add "Quick Start" section

**Deliverable:** `docs/setup.md` updated

---

### PM-S3-04: Create Sprint 4 Plan
**Points:** 10  
**Due:** July 3 (before meeting)

**Steps:**
1. Create `docs/pm/sprint4/README.md`
2. Define Sprint 4 scope:
   - More sources (15+ total)
   - Feedback system
   - Deployment prep
3. Assign tasks to roles
4. Set timeline

**Deliverable:** Sprint 4 plan ready for meeting

---

### PM-S3-05: Run Full Integration Test
**Points:** 5  
**Due:** July 1

**Steps:**
1. Fresh pull of `dev`
2. Start backend, verify /health
3. Start frontend, verify splash screen
4. Test 10 questions from `knowledge/test_questions_week1.md`
5. Verify citations appear
6. Check query logs
7. Document any bugs in `docs/qa/sprint3_bugs.md`

**Deliverable:** Test report with pass/fail

---

## Frontend Tasks (Evan Weber)

### FE-S3-01: Add Dark Mode Toggle
**Points:** 15  
**Due:** July 5

**Steps:**
1. CSS variables already support dark mode (`.dark` class)
2. Add toggle button to Header component
3. Save preference to localStorage
4. Apply `.dark` class to `<html>` element

**Files to edit:**
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/App.tsx` (add state)

**Deliverable:** Working dark mode toggle

---

### FE-S3-02: Add Loading Skeleton for Citations
**Points:** 10  
**Due:** July 4

**Steps:**
1. Use existing `Skeleton.tsx` component
2. Show skeleton cards while `/ask` is loading
3. Replace with real citations when loaded

**Files to edit:**
- `frontend/src/components/chat/ChatBubble.tsx`

**Deliverable:** Skeleton loading for citations

---

### FE-S3-03: Add Error Boundary
**Points:** 10  
**Due:** July 5

**Steps:**
1. Create `frontend/src/components/feedback/ErrorBoundary.tsx`
2. Wrap App in error boundary
3. Show friendly error message if app crashes
4. Add "Reload" button

**Deliverable:** Error boundary component

---

### FE-S3-04: Mobile Input Improvements
**Points:** 5  
**Due:** July 4

**Steps:**
1. Fix keyboard pushing content on mobile
2. Add `safe-area-inset-bottom` padding
3. Test on mobile viewport

**Files to edit:**
- `frontend/src/components/chat/ChatInput.tsx`
- `frontend/src/index.css`

**Deliverable:** Mobile input works correctly

---

## Backend Tasks (Assigned to PM until Landon returns)

### BE-S3-01: Add Rate Limiting to /ask
**Points:** 10  
**Due:** July 5

**Steps:**
1. Install `slowapi` package
2. Add rate limiter to `/ask` endpoint
3. Limit: 10 requests per minute per IP
4. Return 429 if exceeded

**Files to edit:**
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/routers/ask.py`

**Deliverable:** Rate limiting working

---

### BE-S3-02: Add Response Caching
**Points:** 10  
**Due:** July 6

**Steps:**
1. Cache identical questions for 1 hour
2. Use simple in-memory dict cache
3. Return cached response if found
4. Add `cached: true` to response

**Files to edit:**
- `backend/app/routers/ask.py`

**Deliverable:** Caching reduces duplicate API calls

---

### BE-S3-03: Add Health Check Details
**Points:** 10  
**Due:** July 4

**Steps:**
1. Expand `/health` to include:
   - ChromaDB connection status
   - Chunk count
   - Claude API key status (configured/not)
2. Return detailed health object

**Files to edit:**
- `backend/app/routers/health.py`

**Deliverable:** Detailed health endpoint

---

### BE-S3-04: Add Query Analytics Endpoint
**Points:** 10  
**Due:** July 6

**Steps:**
1. Create `GET /ask/analytics`
2. Return:
   - Total queries today
   - Average latency
   - Top 5 questions
   - Success rate
3. Read from query_logs.jsonl

**Files to edit:**
- `backend/app/routers/ask.py`
- `backend/app/services/query_logger.py`

**Deliverable:** Analytics endpoint working

---

## Task Checklist

### PM Tasks
| ID | Task | Points | Due | Status |
|----|------|--------|-----|--------|
| PM-S3-01 | Expand crawler to 5 sources | 15 | Jul 3 | ⬜ |
| PM-S3-02 | Write API docs | 10 | Jul 2 | ⬜ |
| PM-S3-03 | Update setup guide | 10 | Jul 2 | ⬜ |
| PM-S3-04 | Sprint 4 plan | 10 | Jul 3 | ⬜ |
| PM-S3-05 | Integration test | 5 | Jul 1 | ⬜ |

### Frontend Tasks (Evan)
| ID | Task | Points | Due | Status |
|----|------|--------|-----|--------|
| FE-S3-01 | Dark mode toggle | 15 | Jul 5 | ⬜ |
| FE-S3-02 | Loading skeletons | 10 | Jul 4 | ⬜ |
| FE-S3-03 | Error boundary | 10 | Jul 5 | ⬜ |
| FE-S3-04 | Mobile input fix | 5 | Jul 4 | ⬜ |

### Backend Tasks
| ID | Task | Points | Due | Status |
|----|------|--------|-----|--------|
| BE-S3-01 | Rate limiting | 10 | Jul 5 | ⬜ |
| BE-S3-02 | Response caching | 10 | Jul 6 | ⬜ |
| BE-S3-03 | Health check details | 10 | Jul 4 | ⬜ |
| BE-S3-04 | Analytics endpoint | 10 | Jul 6 | ⬜ |

---

## Points Summary

| Role | Total Points | Target |
|------|--------------|--------|
| PM | 50 pts | 50 pts |
| Frontend | 40 pts | 40 pts |
| Backend | 40 pts | 40 pts |
| **Sprint 3 Total** | **130 pts** | **130 pts** |

**Sprint 3 completes v0.3.0 (250 total points)**

---

## Branch Naming Convention

- PM: `feature/pm-s3-XX-description`
- Frontend: `feature/fe-s3-XX-description`
- Backend: `feature/be-s3-XX-description`

Example: `feature/fe-s3-01-dark-mode`

---

## Definition of Done

Each task is DONE when:
1. Code pushed to feature branch
2. PR created with description
3. PR merged to `dev`
4. Tested locally by author
