# Frontend Guidelines — AskMcNeese

The shared rulebook for the frontend. Keeps the UI consistent, on-brand, and safe while the
team grows. Applies to everything under `frontend/`.

## Stack (do not swap without team sign-off)

- **React 18 + Vite + TypeScript** (`.tsx`, strict mode on)
- **Tailwind CSS** for styling — utility classes, no separate CSS frameworks
- Changing any of these is a **team decision**, brought to the PM — not done unilaterally.

## Configuration

- The backend URL comes **only** from `VITE_API_BASE_URL` (in `frontend/.env`, templated by
  `frontend/.env.example`). **Never hardcode** `http://127.0.0.1:8000` in components.
- Only `VITE_`-prefixed env vars are exposed to the browser. Never put secrets in the frontend.

## Branch & PR rules

- Branch off `dev` as `feature/frontend-*`. **Never push to `main`** (reserved for milestones).
- Commits: clear, human messages. **No AI/Cursor watermark.**
- PRs target `dev` and include **screenshots** (mobile + desktop) as proof.

## Brand

- Product name is exactly **"AskMcNeese"**. Attribution is exactly **"Built by McNeese ACM"**.
- Use the McNeese palette via the Tailwind theme: `mcneese.blue`, `mcneese.gold`, `mcneese.dark`.

## UI/UX rules

- **Mobile-first.** It must read well on phone width before any desktop polish.
- **Every async surface handles three states:** empty, loading, and error. No blank screens.
- Keep it simple enough for a new student to understand instantly.

## Components

- One component per file; **PascalCase** names and filenames.
- Reusable pieces live in `src/components/`; data-fetching logic in `src/hooks/`.
- Keep components presentational; lift state up to `App.tsx` or a hook.
- Type every prop with an `interface` — no implicit `any`.

## Content & scope safety (Sprint 1)

- **Demo data must be clearly labeled** (e.g. a "Demo" tag). Never present dummy text as a real answer.
- **No fake institutional answers.** Real answers will be cited from approved sources in a later sprint.
- **Out of scope this week:** dashboards, login/auth, admin panels, citation cards, real answer generation.

## Definition of done (a frontend ticket)

1. Runs locally (`npm run dev`) with no console errors.
2. `npm run build` passes (type-check + bundle).
3. Empty / loading / error states all handled.
4. Mobile and desktop screenshots saved under `docs/screenshots/week1_frontend/`.
5. PR to `dev` with screenshots, reviewed before merge.
