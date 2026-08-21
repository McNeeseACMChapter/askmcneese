# Motion — Implementation Map

**Date:** 2026-07-12

## Packages

| Package | Status |
|---------|--------|
| framer-motion | Keep (Motion owner) |
| lucide-react | Keep (primary icons via AppIcon) |
| gsap + @gsap/react | Installed — scroll sections / methodology / roadmap |
| animejs | Installed — dynamic import in StaggerGroup / Roadmap |
| lottie-web | Installed — wrapper only; no approved asset |
| Tabler / FA / Material / Heroicons | Not installed |
| Lenis / Locomotive / Magic UI package | Not installed |

## Inventory → decision

| Component | Route | Lib | Props | Trigger | Reduced motion | Decision |
|-----------|-------|-----|-------|---------|----------------|----------|
| AmbientSmokePulse | Ask + About | FM | opacity | mount | off | Remain (Ask + quiet About bloom) |
| LiveAnswerProgress phrase | Ask | FM AnimatePresence | opacity/y/blur | stage change | instant text | Remain (approved phrase context) |
| LiveAnswerProgress details | Ask | FM | height/opacity | toggle | instant | Remain |
| CitationGroup expand | Ask | FM | height | toggle | remain | Remain |
| EmptyState | Ask | FM | light enter | mount | remain | Remain |
| About hero | /about | FM | opacity/y | mount | immediate | Remain restrained |
| About BlurFade subtitle | /about | FM | blur/y | mount | immediate | Adapted Magic UI |
| About TextReveal mission | /about | FM | word opacity/y | mount | full phrase | Adapted Magic UI (one sentence) |
| GsapSection reveals | /about | GSAP | opacity/y 16→0 | scroll once | skip | Remain |
| MethodologyStory | /about/methodology | GSAP ST | active step + progress line | scroll | static stacked | Desktop sticky visual; no page pin |
| AnimatedBeam | methodology | CSS/SVG | stroke emphasis | step index | static | Adapted Magic UI |
| TextReveal transition | methodology | FM | words | mount | full phrase | One sentence only |
| StaggerGroup cards | /about/team | Anime.js | opacity/y/scale | IO once | immediate | Remain |
| Advisor RouteEnter | /about/advisor | FM | opacity/y | mount | immediate | Calm only |
| RoadmapTimeline | /about/roadmap | GSAP scrub + Anime | scaleY line; item stagger | scroll | static line | Desktop scrub ≥768 |
| Updates BlurFade + Stagger + layout | /updates | FM + Anime | blur; stagger; layout | mount/filter | immediate | Remain |
| AnimatedMetric | /status | FM | number tween | value change | jump | Real metrics only |
| RouteEnter ops | settings/feedback/acm/status | FM | opacity/y | mount | immediate | Minimal |
| LottieScene | n/a | lottie-web | frames | unused | poster | Blocked — no approved asset |

## Conflicts resolved

- No GSAP + Motion on same transform node (outer `data-gsap-section` / Motion children).
- Anime.js only on `[data-stagger-item]` / `[data-roadmap-item]`, not GSAP parents.
- Methodology Lottie playhead unused (static SVG beam).
- About pages + Updates lazy-loaded; animejs dynamically imported; GSAP chunk separate from Ask entry.
