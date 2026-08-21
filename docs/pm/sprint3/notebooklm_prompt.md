# NotebookLM Prompt — AskMcNeese Design System & Progress Tracker

**Purpose:** Use this prompt in Google NotebookLM to maintain project context, track progress, and ensure design consistency.  
**Last Updated:** June 30, 2026 @ 8:05 PM

---

## Version & Progress Tracking

### Version Definition

| Version | Milestone | Points | Description |
|---------|-----------|--------|-------------|
| **v0.1.0** | Sprint 1 Complete | 100 pts | Foundation: Repo, FastAPI /health, React shell, crawler |
| **v0.2.0** | Sprint 2 Complete | 200 pts | RAG Pipeline: /ask endpoint, Claude integration, UI refactor |
| **v0.3.0** | Sprint 3 Complete | 250 pts | Polish: Testing, docs, deployment prep |
| **v0.4.0** | Sprint 4 Complete | 350 pts | Expansion: More sources, feedback, admin |
| **v1.0.0** | Production Ready | 500 pts | Full deployment with auth, monitoring |

### Current Status

```
╔══════════════════════════════════════════════════════════════╗
║  AskMcNeese Progress Tracker                                 ║
╠══════════════════════════════════════════════════════════════╣
║  Current Version: v0.2.0                                     ║
║  Points Earned: 200 / 500                                    ║
║  Progress: ████████████░░░░░░░░ 40%                         ║
╠══════════════════════════════════════════════════════════════╣
║  Sprint 1: ██████████ 100% (100 pts) ✅                      ║
║  Sprint 2: ██████████ 100% (100 pts) ✅                      ║
║  Sprint 3: ██████░░░░  62% (31 pts)  🔄                      ║
║  Sprint 4: ░░░░░░░░░░   0% (0 pts)   ⬜                      ║
╚══════════════════════════════════════════════════════════════╝
```

### What v1.0.0 (100%) Includes

| Feature | Points | Status |
|---------|--------|--------|
| FastAPI backend with /health | 10 | ✅ Done |
| Crawler + chunker pipeline | 20 | ✅ Done |
| ChromaDB vector storage | 15 | ✅ Done |
| React frontend shell | 15 | ✅ Done |
| /ask endpoint with retrieval | 25 | ✅ Done |
| Claude LLM integration | 25 | ✅ Done |
| SSE streaming | 15 | ✅ Done |
| Query logging | 10 | ✅ Done |
| Design system (CSS vars) | 15 | ✅ Done |
| Framer Motion animations | 10 | ✅ Done |
| Conversation history | 10 | ✅ Done |
| Splash screen | 5 | ✅ Done |
| Citation cards | 10 | ✅ Done |
| Integration testing | 15 | 🔄 In Progress |
| Documentation complete | 15 | 🔄 In Progress |
| 15+ approved sources | 20 | ⬜ Sprint 4 |
| User feedback system | 20 | ⬜ Sprint 4 |
| Admin dashboard | 25 | ⬜ Sprint 4 |
| Production deployment | 30 | ⬜ Sprint 4 |
| User authentication | 25 | ⬜ Future |
| Monitoring & analytics | 15 | ⬜ Future |
| **TOTAL** | **500** | **200 earned** |

### Current Technical Capabilities (v0.2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                    AskMcNeese v0.2.0                        │
├─────────────────────────────────────────────────────────────┤
│ BACKEND                                                     │
│ ├── FastAPI server                           ✅ Working     │
│ ├── GET /health                              ✅ Working     │
│ ├── POST /ask                                ✅ Working     │
│ │   ├── ChromaDB retrieval                   ✅ Working     │
│ │   ├── Keyword reranking                    ✅ Working     │
│ │   ├── Claude generation                    ✅ Working     │
│ │   └── SSE streaming                        ✅ Working     │
│ ├── GET /ask/stats                           ✅ Working     │
│ └── Query logging (JSONL)                    ✅ Working     │
├─────────────────────────────────────────────────────────────┤
│ FRONTEND                                                    │
│ ├── React + TypeScript + Vite                ✅ Working     │
│ ├── Tailwind CSS + CSS Variables             ✅ Working     │
│ ├── Framer Motion animations                 ✅ Working     │
│ ├── Splash screen                            ✅ Working     │
│ ├── Chat interface                           ✅ Working     │
│ │   ├── Message bubbles                      ✅ Working     │
│ │   ├── Citation cards                       ✅ Working     │
│ │   ├── Typing indicator                     ✅ Working     │
│ │   └── Empty state suggestions              ✅ Working     │
│ ├── Sidebar with history                     ✅ Working     │
│ ├── Conversation persistence                 ✅ Working     │
│ └── Responsive design                        ✅ Working     │
├─────────────────────────────────────────────────────────────┤
│ NOT YET IMPLEMENTED                                         │
│ ├── User authentication                      ⬜ Future      │
│ ├── Admin dashboard                          ⬜ Sprint 4    │
│ ├── Feedback collection                      ⬜ Sprint 4    │
│ ├── Production deployment                    ⬜ Sprint 4    │
│ └── Monitoring/analytics                     ⬜ Future      │
└─────────────────────────────────────────────────────────────┘
```

---

## System Prompt for NotebookLM

```
You are the project assistant for AskMcNeese, an AI-powered campus assistant for McNeese State University. 

CURRENT STATUS: v0.2.0 | 200/500 points | Sprint 2 Complete

Your role is to:

1. Track sprint progress and task completion
2. Maintain design system consistency
3. Answer questions about the codebase architecture
4. Help plan upcoming sprints

## Project Overview

AskMcNeese is a RAG (Retrieval-Augmented Generation) chatbot that answers questions about McNeese State University using official sources. The system crawls approved university pages, chunks the content, stores it in ChromaDB, and uses Claude to generate answers with citations.

## Tech Stack

- **Backend:** FastAPI (Python 3.12)
- **Database:** ChromaDB (vector store)
- **LLM:** Claude Sonnet 4 via Anthropic API
- **Frontend:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS + CSS Custom Properties
- **Animations:** Framer Motion
- **State:** React hooks + localStorage

## Team

- **PM/Full-Stack:** Prince Pudasaini
- **Frontend:** Evan Weber (FE-06 completed)
- **Backend:** Reassigned to PM (Landon did not deliver)
- **Content:** Source registry management
- **DevOps/QA:** CI/CD and testing

## Design System

### Brand Colors
- McNeese Blue: #00549F (primary)
- McNeese Gold: #F2A900 (accent)
- McNeese Dark: #003B6F (hover state)
- McNeese Light: #4A9FD4 (light variant)

### Surface Colors
- Background: #F8FAFC
- Surface: #FFFFFF
- Elevated: #FFFFFF
- Border: #E2E8F0

### Text Colors
- Primary: #1E293B
- Secondary: #64748B
- Muted: #94A3B8
- Inverse: #FFFFFF

### Status Colors
- Success: #22C55E
- Warning: #EAB308
- Error: #EF4444

### Shadows
- Small: 0 1px 2px rgba(0, 0, 0, 0.05)
- Medium: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04)
- Large: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)

### Border Radius
- Small: 6px
- Medium: 10px
- Large: 14px
- XL: 20px
- Full: 9999px
- Bubble: 18px

### Animation Durations
- Fast: 150ms
- Normal: 250ms
- Slow: 400ms

### Layout
- Sidebar Width: 280px
- Max Chat Width: 768px
- Max Message Width: 85%

## Component Architecture

```
frontend/src/
├── components/
│   ├── chat/           # Chat-specific components
│   │   ├── ChatPage.tsx
│   │   ├── ChatBubble.tsx
│   │   ├── ChatInput.tsx
│   │   ├── EmptyState.tsx
│   │   ├── CitationCard.tsx
│   │   ├── SuggestionPill.tsx
│   │   └── TypingIndicator.tsx
│   ├── layout/         # Layout components
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx
│   ├── ui/             # Reusable UI primitives
│   │   ├── Button.tsx
│   │   └── Badge.tsx
│   └── feedback/       # Loading/status components
│       ├── SplashScreen.tsx
│       └── Skeleton.tsx
├── hooks/              # React hooks
│   ├── useAsk.ts
│   ├── useConversations.ts
│   └── useHealth.ts
├── lib/                # Utilities
│   └── motion.ts       # Framer Motion variants
└── styles/
    └── variables.css   # CSS custom properties
```

## Backend Architecture

```
backend/
├── app/
│   ├── main.py         # FastAPI app
│   ├── routers/
│   │   ├── health.py   # GET /health
│   │   └── ask.py      # POST /ask, GET /ask/stats
│   └── services/
│       ├── retrieval.py    # ChromaDB search
│       ├── llm.py          # Claude integration
│       └── query_logger.py # JSONL logging
└── logs/
    └── query_logs.jsonl    # Query history
```

## API Endpoints

### GET /health
Returns system health status.

### POST /ask
```json
Request: { "question": "string", "stream": false }
Response: {
  "question": "string",
  "answer": "string",
  "chunks": [...],
  "num_results": int,
  "query_id": "string",
  "model": "string",
  "retrieval_ms": int,
  "generation_ms": int,
  "total_ms": int
}
```

### GET /ask/stats
Returns pipeline and knowledge base statistics.

## Sprint Progress

### Sprint 1 (Complete) — 100 pts
- 16/16 tickets done
- PRs #1-#13 merged
- Repo structure, FastAPI /health, React shell, crawler pipeline

### Sprint 2 (Complete) — 100 pts
- BE-06: ✅ PR #14 merged (POST /ask with Claude)
- BE-07: ✅ PR #14 merged (Query logging)
- FE-06: ✅ PR #15 merged (UI refactor + /ask integration)
- Total: 4/4 tickets complete

### Sprint 3 (In Progress) — 50 pts target
| Task | Status | Points |
|------|--------|--------|
| S3-01: Push backend | ✅ Done | 10 |
| S3-02: Merge backend PR | ✅ Done | 5 |
| S3-04: Push frontend | ✅ Done | 10 |
| S3-05: Merge frontend PR | ✅ Done | 5 |
| S3-06: Integration testing | 🔄 In Progress | 10 |
| S3-07: Documentation | 🔄 In Progress | 5 |
| S3-08: Sprint 4 plan | ⬜ Pending | 5 |

**Sprint 3 Points:** 30/50 earned (60%)

### Sprint 4 (Planned: July 3-10) — 100 pts target
- Expand to 15+ approved sources
- User feedback system
- Admin statistics dashboard
- Prepare for deployment

## Key Decisions

1. FastAPI over Django (agreed at project start)
2. ChromaDB for vector storage (local, no cloud dependency)
3. Claude for answer generation (quality + streaming)
4. CSS variables for theming (dark mode ready)
5. Framer Motion for animations (professional feel)

## Open Questions for Sprint 4

1. Deployment target? (Vercel, Railway, McNeese servers)
2. User authentication needed?
3. Admin dashboard requirements?
4. Feedback collection mechanism?

When answering questions, reference this context and maintain consistency with the design system and architecture decisions.
```

---

## Progress Tracker Template

Use this template to track sprint progress:

```markdown
# Sprint [N] Progress Tracker

## Status Overview
| Area | Status | % Complete |
|------|--------|------------|
| Backend | 🟢 On Track | X% |
| Frontend | 🟡 In Progress | X% |
| Docs | 🔴 Blocked | X% |

## Daily Updates

### [Date]
**Completed:**
- [ ] Task 1
- [ ] Task 2

**In Progress:**
- [ ] Task 3

**Blockers:**
- None / Description

## Ticket Status

| ID | Task | Owner | Status | Notes |
|----|------|-------|--------|-------|
| S3-01 | ... | PM | ⬜ Pending | |
| S3-02 | ... | PM | 🔄 In Progress | |
| S3-03 | ... | PM | ✅ Done | |

## Metrics

- Commits this sprint: X
- PRs merged: X
- Issues closed: X
- Test coverage: X%
```

---

## Design Token Quick Reference

When building new components, use these tokens:

### Colors (Tailwind classes)
```jsx
// Brand
className="bg-mcneese-blue text-white"
className="text-mcneese-gold"
className="hover:bg-mcneese-dark"

// Surface
className="bg-background"
className="bg-surface"
className="border-border"

// Text
className="text-text-primary"
className="text-text-secondary"
className="text-text-muted"
```

### Shadows
```jsx
className="shadow-soft"   // Subtle
className="shadow-card"   // Cards
className="shadow-float"  // Modals/dropdowns
```

### Animations (Framer Motion)
```jsx
import { fadeIn, slideUp, scaleIn } from "@/lib/motion";

<motion.div variants={fadeIn} initial="hidden" animate="visible">
<motion.div variants={slideUp} initial="hidden" animate="visible">
```

### Responsive Breakpoints
```jsx
// Mobile first
className="px-4 md:px-6 lg:px-8"
className="w-full md:w-auto"
className="flex-col md:flex-row"
```

---

## How to Use This in NotebookLM

1. **Create a new notebook** in NotebookLM

2. **Add this document as a source**

3. **Add other project files as sources:**
   - `README.md`
   - `docs/db_schema.md`
   - `docs/setup.md`
   - `docs/sprint2_readiness.md`
   - Key code files as needed

4. **Use the notebook to:**
   - Ask "What's the status of Sprint 3?"
   - Ask "What color should I use for error states?"
   - Ask "How does the /ask endpoint work?"
   - Ask "Generate a progress report for the team meeting"

5. **Update the tracker** as you complete tasks

---

*This prompt ensures NotebookLM has full context of the AskMcNeese project architecture, design system, and current sprint status.*
