# AskMcNeese UI Test Results

**Date:** 2026-07-11  
**Branch context:** local UI overhaul worktree

---

## Baseline (before UI overhaul)

| Check | Result |
|-------|--------|
| Frontend `npm run build` | PASS |
| Backend `unittest discover -s tests/unit` | 8/9 PASS; `test_html_extraction` ERROR — `ModuleNotFoundError: bs4` (pre-existing env gap) |

---

## Post-change

### Frontend

| Check | Result |
|-------|--------|
| `npm run typecheck` | PASS |
| `npm test` (Vitest) | **11/11 PASS** (2 files) |
| `npm run build` | PASS (`tsc --noEmit && vite build`) |

### Backend

| Check | Result |
|-------|--------|
| New: `test_activity_events.py` | PASS (2) |
| New: `test_structured_answer.py` | PASS (4) |
| Existing intent/persona/query_logging | PASS |
| `test_html_extraction` | ERROR — `bs4` missing in `backend/.venv` (pre-existing; not introduced by UI overhaul) |
| Net | **14 PASS / 1 ERROR (pre-existing)** |

---

## Frontend tests covered

- Activity payload mapping and metadata allowlist
- Sensitive message sanitization
- Legacy step → activity mapping
- AskResponse / ChatMessage normalization
- Sidebar collapse localStorage key
- Markdown headings (no visible raw `#`)
- Lists / emphasis rendering
- No-source pattern without empty fact cards
- Conditional important-dates + sources sections

---

## Manual verification still required

- Viewports: 320, 375, 768, 1024, 1280, 1440, 1920
- Zoom: 90%, 100%, 110%, 125%
- Composer does not overlap content at 100% zoom
- Mobile sidebar drawer + focus trap / Escape
- Keyboard-only: nav rail, history search, rename, pin, delete, send, stop
- Live SSE against a running backend with real `/ask` responses
- Reduced-motion preference
- Screen-reader announcement of generating/complete status

---

## Notes

- Streaming is real SSE against `POST /ask` with `stream: true` — not mocked.
- Structured response fields are additive; legacy `answer` remains.
- No ESLint script exists in `frontend/package.json`; typecheck + Vitest + production build were run instead.
