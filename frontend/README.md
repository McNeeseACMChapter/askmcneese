# AskMcNeese Frontend

React + Vite + TypeScript + Tailwind chat UI for the public AskMcNeese assistant.

## What it does

- Chat experience with live activity narration and streaming answers
- Source scope: McNeese knowledge or live web search
- Markdown answers, structured sections, and citation lists from the backend
- Browser-local conversation history (no authentication)
- Public pages: About, Updates, Status, Settings, Feedback

## Run locally

```bash
cd frontend
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
npm install
npm run dev                     # http://localhost:5173
```

Set `VITE_API_BASE_URL` to match the backend. Start the backend first so the
header can show Online.

### Backend port

Default API port is 8000:

```bash
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If 8000 is already in use, run the API on 8001 and set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

## Scripts

```bash
npm run dev          # development server
npm run test         # unit tests
npm run typecheck    # TypeScript check
npm run build        # production bundle
npm run preview      # serve the production build
```

## Structure

```
frontend/src/
├── App.tsx                 # app shell and routes
├── components/chat/        # chat page, answers, citations, composer
├── components/layout/      # header, sidebar, status/settings/feedback
├── components/about/       # about and team pages
├── hooks/                  # ask streaming, conversations, health
├── lib/                    # api helpers, answer model, activity helpers
├── pages/                  # routed screens
└── styles/                 # brand tokens and chat styles
```

## Rules

- Read the backend URL only from `VITE_API_BASE_URL`
- Brand strings: "AskMcNeese" and "Built by McNeese ACM"
- No authentication and no private student dashboards in this app
- Citations and campus facts come from the backend; the UI should not invent them
