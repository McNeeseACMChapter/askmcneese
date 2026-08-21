# Incident report — LinkedIn black-box + UI (2026-07-15)

## Test case (from screenshots)

**Question:** search LinkedIn for Prince Pudasaini at McNeese / any university mention.

**Observed:**
1. Live activity said “campus browse / McNeese-approved” while titles included LinkedIn + Instagram.
2. Answer wrote “LinkedIn profile details” / “Based on public LinkedIn profiles”.
3. Sources listed mcneese.edu + Rate My Professors only — **no LinkedIn URLs**.
4. Pattern label **DEADLINES & DATES** on a person/LinkedIn answer.
5. AskMcNeese identity looked weak; composer pill too wide on desktop.

---

## Root causes (verified in code)

| # | Cause | Location |
|---|--------|----------|
| 1 | `_default_domains()` always included LinkedIn/Instagram even when `social=False` | `perplexity_agentic.py` |
| 2 | Agentic evidence kept any host in the domain filter, bypassing companion allowlist | same file, evidence loop |
| 3 | Full Sonar narrative pasted onto first evidence item → LinkedIn facts rode on McNeese/RMP text | same file |
| 4 | `validate_citations` correctly dropped LinkedIn (no enabled companion) → Sources ≠ evidence | `citations.py` + disabled social CSV |
| 5 | Activity copy always said “campus browse” | `activity_events.py` |
| 6 | `infer_answer_type` treated answer-body DATE_WORDS (`start`, `fall`, `semester`…) as deadlines | `structured_answer.py` |
| 7 | Composer reused `--chat-max-width: 820px` | `ChatInput.tsx` / `variables.css` |

**Not implemented (by design today):** open Google SERP click-through browsing. Live browse is Perplexity Sonar with a **domain filter**, not a general search engine UI. Honest LinkedIn path = domain-scoped LinkedIn + cite the profile URL.

---

## Fixes applied (surgical)

1. **Campus domains only by default**; LinkedIn/social hosts only when `social=True`.
2. **Fail-closed evidence**: keep URL only if official, RMP, or (social + LinkedIn).
3. **Tag LinkedIn** as `SRC-C-LINKEDIN-001` so Sources can list it; registry row enabled.
4. **Plan**: allow social category when the question names LinkedIn/etc. even if global social flag is off.
5. **Activity**: “Searching public LinkedIn…” / “Social / LinkedIn browse returned N…” when social.
6. **Deadline type**: question-intent only — no answer-body DATE_WORDS trap.
7. **Composer**: `--composer-max-width: 40rem`; AskMcNeese header uses editorial type.

---

## Verify

1. Restart backend (companion CSV is cached).
2. Web mode on; ask the LinkedIn/Prince question again.
3. Expect activity to mention LinkedIn when social; Sources to include `linkedin.com/in/...` if returned.
4. No **DEADLINES & DATES** on that answer.
5. Desktop composer narrower than the reading column.
