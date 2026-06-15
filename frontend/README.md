# Frontend — AskMcNeese (Sprint 1)

> Owner: **Evan Weber**
> Stack: **React + Vite + TypeScript + Tailwind CSS**

The AskMcNeese chat shell: a mobile-first interface with dummy messages and a live
`GET /health` connection to the FastAPI backend. **Sprint 1 is a shell only — no real AI answers.**

## Run it locally

```bash
cd frontend
cp .env.example .env       # Windows: copy .env.example .env
npm install
npm run dev                # opens http://localhost:5173
```

The app reads the backend URL from **`VITE_API_BASE_URL`** (see `.env.example`). Start the
backend first (`cd backend` → `uvicorn app.main:app --reload`) to see the header show **Online**.

```bash
npm run build              # type-check + production build
npm run preview            # serve the production build
```

## Sprint 1 tickets (FE-01 → FE-05)

| Ticket | Deliverable | Where |
|--------|-------------|-------|
| FE-01 | React + Vite + Tailwind shell | this folder's config |
| FE-02 | Chat UI shell (list + input + send) | `src/App.tsx` |
| FE-03 | Reusable components | `src/components/` |
| FE-04 | Wire UI to `/health` | `src/hooks/useHealth.ts` + `StatusBadge` |
| FE-05 | Responsive + screenshots | `docs/screenshots/week1_frontend/` |

## Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── MessageBubble.tsx
│   │   ├── ChatInput.tsx
│   │   ├── StatusBadge.tsx
│   │   └── EmptyState.tsx
│   ├── hooks/
│   │   └── useHealth.ts
│   ├── data/sampleMessages.ts
│   ├── App.tsx
│   ├── main.tsx
│   ├── types.ts
│   └── index.css            # Tailwind directives
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── vite.config.ts
└── .env.example
```

## Rules

See **`docs/frontend_guidelines.md`** for the full rulebook. Key points:

- Read the backend URL only from `VITE_API_BASE_URL` — never hardcode it.
- Brand strings are exact: **"AskMcNeese"** and **"Built by McNeese ACM"**.
- Every async UI handles empty / loading / error states.
- Demo data must be clearly labeled. No fake institutional answers.
- **Sprint 2** wires Send → `POST /ask` — see `docs/sprint2_readiness.md`.
