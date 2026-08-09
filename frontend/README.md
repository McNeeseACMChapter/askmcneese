# AskMcNeese Frontend

React, Vite, TypeScript, Tailwind, and motion-powered client for the public AskMcNeese beta.

> **Beta sprint completed 2026-08-08.** Interface details and behavior may change when production bugs or accessibility issues are found.

## Routes

| Route | Experience |
| --- | --- |
| `/ask` | Streamed campus questions, activity trail, answers, and citations |
| `/class-planner` | Course search, section fit, local schedule, and week visualization |
| `/about` | Product story, method, and contributor presentation |
| `/updates` | Product changes and release notes |
| `/status` | Usage and service information |
| `/settings` | Browser-local preferences and walkthrough replay |
| `/feedback` | User feedback handoff |
| `/acm/login` | Redirect boundary for the separate ACM Panel |

## Current capabilities

- Responsive desktop, tablet, and phone application shell
- Browser-local conversations and Class Planner schedules
- Streaming answers with sanitized activity states
- Structured answer rendering and accessible citation links
- Adaptive source modes passed to the backend
- Anonymous guest bootstrap with a mandatory 14-step guided walkthrough
- Replayable onboarding that preserves the same guest identity
- Class Planner API modes: `mock`, `staging`, and `live`
- Reduced-motion support, keyboard-aware dialogs, and responsive navigation

The client does not manufacture campus facts or silently replace failed staging/live planner data with samples. Evidence, citations, class records, freshness, and authoritative status come from the backend.

## Run locally

```powershell
cd frontend
npm install
npm run dev
```

Default URL: <http://127.0.0.1:5173>

Configure:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_CLASS_DATA_MODE=mock
VITE_CLASS_TERM_ID=202660
```

Use `staging` or `live` only when the backend has a validated published class dataset.

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start Vite development mode |
| `npm run test` | Run Vitest once |
| `npm run test:watch` | Run Vitest in watch mode |
| `npm run typecheck` | Run TypeScript without emitting files |
| `npm run build` | Typecheck and create the production bundle |
| `npm run preview` | Serve the production bundle locally |

## Architecture

```text
src/
|-- App.tsx                         routes and application orchestration
|-- components/chat/               Ask conversation, answers, citations, composer
|-- components/shell/              desktop, tablet, and mobile application shell
|-- components/about/              contributor story and responsibility flow
|-- features/class-planner/        planner state, API, time model, UI, and tests
|-- features/onboarding/           guest tour state machine, persistence, and UI
|-- hooks/                          Ask, conversations, health, and local preferences
|-- lib/                            API and presentation utilities
|-- pages/                          routed public screens
`-- styles/                         brand, shell, About, and responsive CSS
```

## Walkthrough behavior

The canonical tour has 14 conceptual steps. It advances from real route, menu, click, and About-scroll state rather than decorative Next buttons. Desktop expands the conversation area only for its tour checkpoint; mobile uses the real menu and History sheet. Progress writes are queued and deduplicated, and only bootstrap/final-save failures interrupt the visitor.

## Class Planner behavior

- Search is debounced before API requests.
- Existing results remain visible during refresh.
- Empty first-load uses a compact three-row skeleton.
- Desktop result and schedule panes contain their own overflow.
- Mobile separates Find and Week while preserving one schedule state.
- Conflicts, credits, meeting dates, live-time projection, and fit explanations are deterministic.

## UI rules

- Use `BrandLogo` and the approved assets in `public/assets/brand/`.
- Keep AskMcNeese public UI separate from `acm/frontend`.
- Use source-backed wording; never imply that AI is the university authority.
- Do not expose private data or add controls without a working destination.
- Preserve keyboard focus, semantic roles, minimum touch targets, and reduced motion.
- Test desktop and phone layouts whenever shell, planner, About, or walkthrough styles change.

## Related documentation

- [`../docs/BETA_SPRINT_COMPLETION.md`](../docs/BETA_SPRINT_COMPLETION.md)
- [`../docs/onboarding/README.md`](../docs/onboarding/README.md)
- [`../docs/class-planner/README.md`](../docs/class-planner/README.md)
- [`../docs/BRAND_LOGO_RULES.md`](../docs/BRAND_LOGO_RULES.md)
