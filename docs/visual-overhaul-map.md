# Visual Overhaul — Implementation Map

**Date:** 2026-07-12  
**Constraint:** Preserve stabilized Ask SSE lifecycle, citations, activity events, and `useAsk`.

---

## 1. Application shell & routing

| Field | Detail |
|-------|--------|
| Current component | `App.tsx` + `AppView` local state |
| Current visual responsibility | Single-page swap between chat / status / settings / feedback |
| Confirmed weakness | No deep links, no browser history, no About/Updates, chat history sidebar on all views |
| Target visual behavior | Nested public routes under one glass shell; contextual sidebar; mobile bottom nav (Ask / About / Updates / More) |
| Exact files to change | `main.tsx`, `App.tsx`, `types.ts`, new `routes/*`, new `components/shell/*`, `NavRail.tsx`, `Sidebar.tsx`, `Header.tsx` |

---

## 2. Design tokens

| Field | Detail |
|-------|--------|
| Current component | `variables.css`, `tailwind.config.js`, `chat-glass.css` |
| Current visual responsibility | Brand blues, gold, single glass family, 4px spacing |
| Confirmed weakness | No semantic canvas/glass-level roles; flat canvas; motion tokens incomplete; chat column 760px |
| Target visual behavior | Semantic color roles, 3 glass levels, ambient background, motion tokens, `--chat-max-width: 820px`, page gutters |
| Exact files to change | `variables.css`, `index.css`, `chat-glass.css`, `answer-typography.css`, `tailwind.config.js` |

---

## 3. Icon system

| Field | Detail |
|-------|--------|
| Current component | Inline hand-drawn SVG paths in NavRail, Header, EmptyState, etc. |
| Current visual responsibility | Ad-hoc icons |
| Confirmed weakness | Mixed stroke weights; no shared icon package |
| Target visual behavior | `lucide-react` only; 20/16/24/28 sizes; stroke 1.75 / active 2 |
| Exact files to change | New usage across shell + chat + about; install `lucide-react` |

---

## 4. Ask empty state

| Field | Detail |
|-------|--------|
| Current component | `EmptyState.tsx` |
| Current visual responsibility | Brand mark + 3 suggestion cards |
| Confirmed weakness | Card-heavy; weak editorial hierarchy; only 3 prompts |
| Target visual behavior | Editorial entry: mark, headline, one line, composer-aligned prompts (4), methodology link |
| Exact files to change | `EmptyState.tsx` |

---

## 5. User prompt

| Field | Detail |
|-------|--------|
| Current component | `ChatBubble.tsx` + `.userMessage` |
| Current visual responsibility | Right-aligned glass bubble |
| Confirmed weakness | Uses editorial font; padding not on scale |
| Target visual behavior | Source Sans; blue glass; 16–18px pad; 18–22px radius; ~70–78% max |
| Exact files to change | `chat-glass.css`, `ChatBubble.tsx`, `variables.css` |

---

## 6. Live Answer Progress

| Field | Detail |
|-------|--------|
| Current component | `TypingIndicator.tsx` + `ActivityTimeline.tsx` |
| Current visual responsibility | Compact activity bubble; optional collapse |
| Confirmed weakness | Collapsible while active; bouncing dots as primary UX |
| Target visual behavior | Always-expanded `LiveAnswerProgress` while active; real events only; completion summary after |
| Exact files to change | New `LiveAnswerProgress.tsx`; update `ActivityTimeline.tsx`, `TypingIndicator.tsx`, `ChatPage.tsx`, `AssistantMessage.tsx` |

---

## 7. Assistant answer article

| Field | Detail |
|-------|--------|
| Current component | `AssistantMessage.tsx`, `SemanticAnswer.tsx`, `MessageActions.tsx` |
| Current visual responsibility | Glass answer + copy action |
| Confirmed weakness | Thin identity row; actions hover-only; limited feedback actions |
| Target visual behavior | Editorial article frame; lead typography; Copy / Helpful / Not helpful / View sources |
| Exact files to change | `AssistantMessage.tsx`, `MessageActions.tsx`, `SemanticAnswer.tsx`, `answer-typography.css` |

---

## 8. About & Updates

| Field | Detail |
|-------|--------|
| Current component | None |
| Current visual responsibility | N/A |
| Confirmed weakness | No product story, trust funnel, or changelog surface |
| Target visual behavior | `/about` + subpages; `/updates` from real repo milestones |
| Exact files to change | New `pages/about/*`, `pages/UpdatesPage.tsx`, `content/updates.ts`, `content/about.ts` |

---

## 9. Status / Settings / Feedback

| Field | Detail |
|-------|--------|
| Current component | `SystemStatusPanel`, `SettingsPanel`, `FeedbackPanel` |
| Current visual responsibility | Operational panels |
| Confirmed weakness | Not route-addressable; inconsistent glass/chrome |
| Target visual behavior | Same panels on `/status`, `/settings`, `/feedback` under shell |
| Exact files to change | Wire via routes; light visual alignment only |

---

## 10. Responsive & a11y

| Field | Detail |
|-------|--------|
| Current component | Bottom bar NavRail on mobile; drawer sidebar |
| Current visual responsibility | Mobile chrome |
| Confirmed weakness | Too many bottom items; no More sheet; reduced-transparency incomplete |
| Target visual behavior | 4-item bottom nav; More sheet; rail+sidebar desktop; reduced motion/transparency |
| Exact files to change | `MobileNavigation.tsx`, shell CSS, `variables.css` media queries |

---

## Execution order

A → routes/shell · B → tokens/icons · C → Ask · D → About/Updates · E → responsive/a11y · F → tests/docs
