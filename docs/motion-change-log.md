# Motion — Change Log

**Date:** 2026-07-12  
**Scope:** Non-chat public routes motion + scroll storytelling. Ask SSE lifecycle unchanged.

## Packages added

- `gsap`, `@gsap/react`
- `animejs`
- `lottie-web` (wrapper only)

## Packages deliberately not added

- Magic UI npm package
- Lenis / Locomotive Scroll
- `@tabler/icons-react`, Heroicons, Font Awesome, Material Symbols
- Second Motion package (`motion` alongside `framer-motion`)

## Animation ownership

| Engine | Owns |
|--------|------|
| GSAP + ScrollTrigger | About section reveals, Methodology active step + progress, Roadmap scrub line |
| Framer Motion | Heroes, RouteEnter, BlurFade, TextReveal, layout filters, Live progress phrases, AnimatedMetric |
| Anime.js | Team card stagger, Updates row stagger, Roadmap milestone detail stagger (once) |
| Lottie | Blocked — no approved JSON |
| CSS | Focus, hover color, beam stroke states |

## Routes enhanced

- `/about` — Motion hero + GSAP sections + BlurFade + one TextReveal mission line
- `/about/methodology` — sticky desktop visual + ScrollTrigger steps + AnimatedBeam
- `/about/team` — Anime.js StaggerGroup
- `/about/advisor` — Motion RouteEnter only
- `/about/roadmap` — GSAP progress + Anime once-active details
- `/updates` — BlurFade heading + Anime stagger + Motion layout filters
- `/status` — AnimatedMetric on real API numbers
- `/settings`, `/feedback`, `/acm/login` — short RouteEnter (+ BlurFade on ACM intro)

## Magic UI adapted (local)

- `BlurFade.tsx`
- `TextReveal.tsx`
- `AnimatedBeam.tsx`

## Icon governance

- Primary: `lucide-react` via `AppIcon`
- Tabler fallback count: 0

## Lottie

- `LottieScene.tsx` present; Methodology uses static SVG/CSS beam until approved asset exists.

## Bundle impact (production build)

| Chunk | Approx size |
|-------|-------------|
| Main `index-*.js` | ~560 kB / ~176 kB gzip (down from ~608 before Updates/anime split) |
| `gsap-*.js` | ~116 kB / ~46 kB gzip — loaded with About scroll routes |
| `AboutMethodology-*.js` | ~5 kB |
| `UpdatesPage-*.js` | ~11 kB |
| Anime.js | dynamic import from StaggerGroup/Roadmap — not in Ask entry |

About / Methodology / Team / Roadmap / Updates are `React.lazy`. Ask does not import MethodologyStory or GSAP eagerly.

## Criticism loop removals

1. **Motion excess** — Removed double BlurFade+TextReveal on About hero; TextReveal limited to one mission sentence + one Methodology transition. No page-wide pin (sticky column only).
2. **Library conflict** — Wrapper separation enforced; anime dynamic import; no GSAP on stagger children.
3. **Reading quality** — Content visible before GSAP init; failsafe reveal on StaggerGroup; no 60–100px entrances.
4. **Mobile** — Pinning disabled; methodology stacks; roadmap static line below 768.
5. **Accessibility** — Reduced-motion zeros durations; AnimatedMetric announces final value only; methodology steps always in DOM order.

## Tests

- `frontend/src/motion.test.tsx` (+ existing suite): 64 frontend tests pass
- Backend: 18 unit tests pass

## Remaining limitations

- No approved Lottie asset for methodology scene
- Full-page Playwright captures may duplicate sticky header mid-scroll (stitch artifact)
- Main bundle still large (framer-motion + chat) — further Ask-only splitting not in this pass
- 200% zoom pin disable relies on width matchMedia (1024), not explicit zoom API
