# Chain of command — About Team (2026-07-15)

## Intent
Show AskMcNeese governance as a readable hierarchy, not a flat roster: ACM umbrella → advisor → PM → builders.

## Hierarchy (source of truth: `content/orgChart.ts`)
1. **McNeese ACM** — organizational home (logo slot)
2. **Kody Vo** — Chapter President (aligned under ACM, works with PM)
3. **Dr. Vipin Menon** — Project Advisor; vision/sprint validator
4. **Prince Pudasaini** — Project Manager (since start)
5. Same row: **Landon Peurta** (former backend, faded), **Ziyan** (backend, current), **Evan Weber** (frontend, current)

## Layout split
| Viewport | Pattern |
|----------|---------|
| ≥768px | CSS tree with stems + 3-column builder row |
| &lt;768px | Left-rail timeline rows (not scaled-down tree cards) |

## Interaction
- Hover/focus lift on desktop cards; photo slight scale
- Former contributor: reduced opacity + desaturate, badge `Former · …`
- Framer `whileInView` stagger; respects `prefers-reduced-motion`

## Photos
Drop portraits into `public/about/team/`:
`kody-vo.jpg`, `vipin-menon.jpg`, `prince-pudasaini.jpg`, `landon-peurta.jpg`, `ziyan.jpg`, `evan-weber.jpg`.
Missing files fall back to initials. ACM uses `acm-logo.svg`.
