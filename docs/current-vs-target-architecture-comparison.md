# Current vs Target Architecture Comparison

**Date:** 2026-07-12  
**Rule:** A difference from a future target is not automatically a problem.  
**Inputs:** Verified code (`docs/current-system-evidence-map.md`), `docs/ARCHITECTURE.md`, `docs/DESIGN_SYSTEM.md`, this prompt’s future multi-role model (reference only).

---

## Comparison Table

| Area | Current verified implementation | Current problem | Target concept | Does target solve current problem? | Migration cost | Dependency | Recommendation | Implementation timing |
|------|---------------------------------|-----------------|----------------|------------------------------------|----------------|------------|----------------|----------------------|
| Routing | Flat `AppView` state; no react-router | None for current 4 views | Route groups: public/auth/account/student/workspace | No — adds complexity without fixing Ask defects | High | Auth contracts | Keep flat SPA views | Reject for now / Long-term option |
| Auth | Absent | Blocks accounts/roles only | Auth boundary layouts | N/A — no Ask P0/P1 | High | Identity provider | Do not fake login | After product approval + After authentication |
| Ask API | `POST /ask` stream+structured | Defaults/docs mismatch; large router | Thin routers + services | Partially (maintainability) | Medium | Test coverage | Stabilize Ask UX first; split ask.py later | After core stabilization |
| Streaming UX | SSE client; UI waits for done | Trust/latency (P1-1) | Live token render | Yes | Low–Medium | App message state | Wire existing callback | Now |
| Citations | Real URLs via SSE/chunks | Title-only dedupe | Source cards + claim mapping | Partially (dedupe/mapping) | Low | — | Fix dedupe; claim-level mapping later | Now (dedupe); After product approval (claim map) |
| Status narration | Backend activity + FE fallbacks | Message map drift | Safe stage narration | Already mostly there | Low | — | Align maps | Now |
| Design tokens | Central CSS variables + glass + answer type | Minor doc lag; contrast unmeasured | Possibly different blur/radius values | No — changing tokens without evidence harms coherence | Medium | Visual QA | Preserve tokens; measure contrast | After core stabilization (only if fail) |
| Glassmorphism | Composer, bubbles, nested panels | Unmeasured contrast/perf | Broader glass | No | — | — | Keep current family; avoid more nested glass | Now (preserve) |
| `common/` package | Missing; duplicated HTML helpers possible | Maintainability | Shared html/http/text/registry | Yes for crawler/backend parity | Medium | Crawler+backend | Optional cleanup | After core stabilization |
| `web_search/` split | Single large module | Size | Folder modules | Yes for maintainability | Medium | ask.py imports | Defer | After core stabilization |
| Integration tests | Absent | Hard to catch stream regressions | `backend/tests/integration/` | Yes | Medium | Running stack | Add Ask smoke | After core stabilization |
| Student dashboard | Not present | None (not in scope) | Student shell | No current Ask problem | High | Auth + APIs | Not justified | Future roadmap only |
| ACM workspace | Mailto only | None | ACM dashboard / publishing | No | High | Auth + APIs | Not justified | Future roadmap only |
| Conversation storage | Browser localStorage | No cross-device; loss on clear | Server-backed history | Only if accounts exist | High | Auth + DB | Defer | After authentication |
| related_questions | Always null | Empty UI capability | Generated follow-ups | Product enhancement | Medium | LLM contract | Do not fabricate client-side | After backend contract |
| Multi-role IA | Single public Ask | None for MVP | Multi-portal | No | Very high | Auth, APIs, ownership | Reject until Ask stable | Long-term option |

---

## Route Readiness (proposed future routes)

| Route / capability | Classification | Contract status | Notes |
|--------------------|----------------|-----------------|-------|
| Public Ask (current chat view) | Existing but needs correction | Ready and verified | P1 streaming/error/citations |
| System status | Existing and stable | Ready and verified | Uses `/ask/stats` |
| Settings | Existing and stable | Ready (client prefs) | localStorage only |
| Feedback | Existing and stable | Ready (mailto) | No API |
| `/about/roadmap` | Ready to build (docs-only) | Not required | Optional communication; not blocking |
| Student dashboard | Future roadmap only | Not available | Do not ship empty shell |
| ACM workspace | Future roadmap only | Not available | Do not ship empty shell |
| Auth / account | Blocked by authentication | Not available | — |
| Automation / publish controls | Blocked by API | Not available | — |

---

## Design-Token Preservation Decision

| Decision | Rationale |
|----------|-----------|
| **Retain** current brand, surface, typography, glass, and chat-body tokens | Consistent across composer/bubbles/answers; DESIGN_SYSTEM aligns; no evidence yet that blur 18px or radius 20px fails usability |
| **Do not** introduce a second token system or aspirational replacements | Violates preservation gate |
| **Measure** contrast and reduced-transparency readability | Only change glass opacity/blur if measurement fails |

---

## Analytical Conclusion

The largest gaps between “target platform” and “repository reality” are **authentication**, **multi-role route groups**, and **server-backed account features**. None of these fix the verified Ask-flow P1 defects.

The highest-value near-term work is **completing the existing Ask SSE path in the UI**, **surfacing errors**, **fixing citation dedupe**, and **aligning operator-facing docs/strings** — not restructuring the repository into public/auth/student/workspace trees.
