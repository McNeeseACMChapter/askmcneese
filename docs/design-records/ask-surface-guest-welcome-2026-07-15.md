# Ask surface design record — guest welcome

**Date:** 2026-07-15  
**Surface:** Ask empty state (`EmptyState` + welcome tokens)  
**Emulator:** `ask-surface-research-emulator.canvas.tsx`  
**Status:** Iteration 1 shipped (research-prescribed)

---

## Problem

The Ask content surface read as cold plain white. Hierarchy did not match how guests scan a first paint: brand warmth, clear path to ask, optional help, then trust. Risk of either (a) utility chill or (b) dark-pattern steering before the user has spoken.

## Non-manipulation rule

Welcome and affordances may raise **ability** (Fogg) and cut **extraneous load** (Sweller). They must not invent goals, fake urgency, or push a product agenda before the guest asks. Starters are optional, never obligatory.

## Screen zone map (first viewport)

| Priority | Zone | User should perceive | Applied |
|---|---|---|---|
| **P0** | Brand + warm greeting | “I am welcome; this is McNeese” | Hero `AskMcNeese` + “Welcome — you're in the right place.” |
| **P1** | Composer (docked) | “I can ask anything” | Unchanged dock; empty state does not compete |
| **P2** | Optional starters (≤4) | “If stuck, light ideas” | Label: “Optional places to start”; large hit targets |
| **P3** | Trust / methodology | “How answers are grounded” | Single quiet footer link |

## Research basis (≥10)

1. **Sweller (1988)** — Cognitive Load Theory → cut extraneous chrome on first paint  
2. **Miller (1956)** — Working memory → ≤4 starters  
3. **Hick (1952)** — Choice RT → fewer options, faster first ask  
4. **Fitts (1954)** — Target acquisition → large starter targets near composer  
5. **Gestalt proximity** — Welcome cluster separate from starters  
6. **Tractinsky (1997/2000)** — Aesthetic-usability → warm surface raises perceived trust  
7. **Norman (2004)** — Emotional design → visceral warmth without coercion  
8. **Weiser & Brown (1996)** — Calm technology → trust + starters stay peripheral  
9. **Fogg (2003)** — Behavior model → raise ability; no coercion  
10. **Nielsen (1994)** — Match the real world → campus language, guest welcome  
11. **Hassenzahl (2003)** — Hedonic quality → pleasure supports continued use  
12. **Whitenton / NN/g** — Minimize cognitive load → one job per zone  

## Preference emulator outcome (iteration 1)

Research prescription applied as shipping default (votes in canvas for live feedback):

- **Ship:** warm welcome + sparse starters + peripheral trust + composer primacy  
- **Reject:** plain white utility + suggestion walls that pre-define intent  

## Token / code map

| Concern | Location |
|---|---|
| Welcome tokens | `frontend/src/styles/variables.css` (`--ask-welcome-*`, `--ask-starter-*`) |
| Welcome CSS | `frontend/src/index.css` (`.ask-welcome*`, `.suggestion-row`) |
| Empty composition | `frontend/src/components/chat/EmptyState.tsx` |
| Welcome column flag | `ChatPage` → `chatColumn--welcome` |

## Iteration log

| Iter | Change | Result |
|---|---|---|
| 0 | Flat white + “Suggested questions” | Cold; intent framing felt quiz-like |
| **1** | Atmosphere wash, warm greeting, optional starters, tokens, emulator + this record | Shipped; gather live votes in canvas |
| **1b** | Composer pill compact: drop header row, pad 8/12, send 36px, textarea max 112 | Addresses “pill way bigger” feedback |
| **2** | Mobile calm: chip starters (3), hide support/trust/label, soft nav gold, single-row composer | Cut noise; keep one greeting row |
| **2b** | Phone composer restructure: one flex row Smart\|field\|send; kill absolute send + tall empty pad | Fixes broken phone pill |
| **3** | Readable chat + nav: fit-content user bubble, History in capsule, Updates/Status→More, drop Methodology/Roadmap dupes | Eyeball + IA cleanup |

## Next iteration triggers

- Emulator leading preference flips away from warm welcome  
- Guest testing: greeting feels manipulative or brand is overpowered  
- Mobile: atmosphere clips or starters fight composer focus  
- Accessibility: contrast / reduced-transparency regressions  

Record votes and outcomes here before shipping iteration 2.
