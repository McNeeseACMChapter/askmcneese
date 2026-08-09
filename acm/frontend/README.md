# ACM Panel frontend

> **Prototype status:** fixture-backed and separate from the public AskMcNeese beta. Subject to change before any production use.

Self-contained visual foundation for **McNeese ACM · Internal operations**.

Lives only under `askmcneese/acm/frontend/`. Does **not** import AskMcNeese public app components or styles.

## Run

```bash
npm install
npm run dev
```

Dev server is pinned to **http://127.0.0.1:3100** (`strictPort`).  
AskMcNeese public app owns **:5173**. Do not use 5173 or 5174 for ACM (5174 is often Windows-reserved).

Open `/login` or `/home`. From Ask, `/acm/login` redirects here after demo verification.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Dev server |
| `npm run build` | Typecheck + production build |
| `npm run preview` | Preview `dist/` |
| `npm run test` | Vitest unit/UI tests |
| `npm run typecheck` | TypeScript project build |
| `npm run lint` | ESLint |

Screenshots (after `npm run build` and preview on port 4173):

```bash
npx vite preview --host 127.0.0.1 --port 4173
node scripts/capture-viewports.mjs
```

Artifacts land in `artifacts/visual/`.

## Design docs

- [`DESIGN_AUDIT.md`](./DESIGN_AUDIT.md)
- [`DESIGN_CONTRACT.md`](./DESIGN_CONTRACT.md)
- [`INFORMATION_ARCHITECTURE.md`](./INFORMATION_ARCHITECTURE.md)
- [`PAGE_PATTERNS.md`](./PAGE_PATTERNS.md)
- [`RESPONSIVE_RULES.md`](./RESPONSIVE_RULES.md)
- [`VISUAL_QA.md`](./VISUAL_QA.md)
- [`IMPLEMENTATION_RECORD.md`](./IMPLEMENTATION_RECORD.md)

## Prototype notice

All data is fixture-only. Login does not authenticate. Approval buttons only emit local feedback.
