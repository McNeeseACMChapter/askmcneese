# Visual Overhaul — Change Log

**Date:** 2026-07-12  
**Scope:** Design-led public product shell, Ask visual system, About/Updates storytelling. Backend Ask SSE lifecycle unchanged.

---

## Visual Correction Pass — 2026-07-12 (evening)

### Borders removed
- Dropped dual rail+sidebar separators; composer inner divider; action-row rules; Official sources heading block; suggestion card borders; answer glass card chrome for body content.
- Sidebar uses tonal navy surface instead of stacked pale bordered columns.

### Navigation consolidated
- Replaced `NavigationRail` + `ContextSidebar` with one `UnifiedSidebar` (260px expanded / 72px collapsed).
- Text-first primary nav; icons only when collapsed; ACM Portal in sidebar, header, and mobile More.

### Brand icons removed
- No invented AskMcNeese logo, sparkles, or AI glyphs in empty state, progress, or shell.
- Wordmark is typographic: EB Garamond **AskMcNeese** only.

### Live-progress behavior changed
- Compact ~56–68px row by default; Details expands/collapses with motion.
- Stage text crossfades via AnimatePresence; events grouped into display phases.
- Sub-100ms times omitted; no duplicate Stop; no sparkle mark.

### Duplicate controls removed
- Stop only in composer (Send ↔ Stop).
- Sources only as `Sources · N` disclosure (no View sources / Official sources).

### Typography corrected
- EB Garamond: wordmark + editorial titles.
- Source Sans: nav, prompts, body, progress, composer, metadata, header labels.

### Scroll ownership corrected
- Global `overflow: hidden` removed from html/body/#root.
- Ask keeps internal conversation scroller + sticky composer.
- About/Updates/Status use natural document scroll.

### Composer caution added
- Visible trust warning under composer; shortcuts moved to sr-only / Send tooltip.

### Source interaction consolidated
- `CitationGroup` control reads `Sources · N`; expands to typographic list.

### ACM Portal route added
- `/acm/login` (+ `/workspace/login` redirect). Honest unavailable auth state.

### Smoky motion added
- `AmbientSmokePulse` on empty-state entrance and submit; disabled under reduced motion/transparency.

### Screenshots captured
- `docs/screenshots/visual-correction/` at 390 / 768 / 1280 / 1440 for empty Ask, progress compact/expanded, answer+sources, About, Updates, ACM Portal, mobile More.

### Tests run
- Frontend 51 passed; backend 18 passed; typecheck/build pass.

### Remaining limitations
- Helpful/Not helpful remain local-only acknowledgements.
- Live SSE mid-stream screenshots used `/__visual__/*` harness (real components + fixture activity); end-to-end live backend stream not required for this visual pass.
- Legacy `NavigationRail.tsx` / `ContextSidebar.tsx` / `Header.tsx` files unused (cleanup candidates).
- Official product logo still pending; text wordmark is temporary.

---

## Routes added

| Route | Purpose |
|-------|---------|
| `/` | Redirect → `/ask` |
| `/ask` | Public Ask experience |
| `/about` | Product story & trust funnel |
| `/about/team` | Contribution areas (role-based) |
| `/about/advisor` | Project Advisor section |
| `/about/methodology` | Retrieval, citation, limits |
| `/about/roadmap` | Completed / Current / Next / Future |
| `/updates` | Real milestone feed from local registry |
| `/status` | System status panel |
| `/settings` | Client preferences |
| `/feedback` | Feedback panel |
| `/acm/login` | ACM Portal (auth not enabled in this build) |
| `/workspace/login` | Redirect → `/acm/login` |
| `/*` | Polished 404 |

Router: `react-router-dom` with nested layout under `PublicAppShell`. Ask conversation state remains in `App` above route outlets so navigation preserves history.

---

## Components added

- `PublicAppShell`, `NavigationRail`, `ContextSidebar`, `MobileNavigation`, `RouteHeader`, `GlassSurface`
- `IconButton`
- `LiveAnswerProgress`
- About helpers: `ContributorAreaCard`, `AboutProcess`, `AdvisorFeature`, `RoadmapTimeline`
- `UpdateCard`
- Pages: About layout + subpages, `UpdatesPage`, `NotFoundPage`
- Content: `content/about.ts`, `content/updates.ts`

## Components changed

- `App.tsx` — BrowserRouter + route tree; Ask state preserved
- `ChatPage.tsx` — reading column width; Live Answer Progress placement above assistant
- `EmptyState.tsx` — editorial entry + 4 prompts + methodology link
- `AssistantMessage.tsx`, `MessageActions.tsx` — identity row + Copy / Helpful / Not helpful / View sources
- `Sidebar.tsx` — glass chrome + New conversation
- `SemanticAnswer.tsx` — `data-sources` for View sources scroll
- Legacy `NavRail` / `Header` retained but no longer mounted by App

## Tokens changed

- Semantic roles: `--color-canvas*`, `--color-glass-*`, `--color-brand-*`, `--color-text-*`, `--color-border-*`, `--color-status-*`
- Glass levels: nav / content / interactive blur & opacity
- Motion: `--motion-instant|fast|standard|panel|emphasis` + easings
- Layout: `--chat-max-width: 820px`, `--page-gutter` breakpoints, `--bottom-nav-height`
- Type hierarchy tokens (`--type-display` … `--type-metadata`)
- Body answer font → Source Sans; titles remain EB Garamond
- Ambient `.app-atmosphere` background + grain; reduced transparency / print fallbacks

## Icons added

- Package: `lucide-react` (single icon family)
- Navigation, progress, About, Updates, actions use Lucide at 16/20/24/28 with stroke 1.75 (active nav 2)

## Motion rules

- Live progress pulse + spinner respect `prefers-reduced-motion` (durations zeroed via CSS vars)
- Framer route/list motions keep existing spring helpers
- No token-by-token answer animation

## Responsive behavior

- `<768px`: bottom nav (Ask / About / Updates / More), no persistent sidebar, More sheet
- `768–1023`: rail + optional sidebar overlay
- `1024+`: rail + contextual sidebar
- Ask column: `min(calc(100% - 2*gutter), 820px)`

## Accessibility behavior

- `NavLink` `aria-current="page"`
- Icon-only controls: `aria-label` + title + ≥44px targets
- Live Answer Progress: `role="status"`, `aria-busy`, polite live region, completed stage list
- Reduced transparency solidifies glass surfaces

## Tests

- `routes.visual.test.tsx` — NavLink active states, About, 404, Live progress expand/complete
- `ask-route-state.test.tsx` — Ask state preserved across route changes
- `live-progress-a11y.test.tsx` — accessible progress without motion dependency
- Existing stabilization suites retained (45 frontend tests passing)

## Screenshots / validation evidence

See `docs/visual-overhaul-validation.md` (automated + manual matrix status).

## Known limitations

- Helpful / Not helpful is local UI state only (no backend feedback API yet)
- Manual device/zoom matrix not fully screenshot-captured in CI
- Old `NavRail.tsx` / `Header.tsx` unused by App (candidates for later cleanup)
- Updates are a typed local registry, not a CMS
- No invented advisor/person names; advisor section is role-based
