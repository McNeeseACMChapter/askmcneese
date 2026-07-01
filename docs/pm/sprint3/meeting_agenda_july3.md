# Team Meeting Agenda — July 3, 2026

**Date:** Thursday, July 3, 2026  
**Time:** 1:00 PM – 3:00 PM (2 hours)  
**Location:** Drew Hall, McNeese State University  
**Facilitator:** Prince Pudasaini (PM)

---

## Meeting Objectives

1. Review all progress from Sprint 1, 2, and 3
2. Live demonstration of AskMcNeese
3. Plan Sprint 4 tasks and assignments
4. Address any blockers or concerns

---

## Agenda

### 1. Welcome & Check-in (5 min)
- Attendance
- Any urgent items to add

---

### 2. Sprint Progress Review (30 min)

#### Sprint 1 Recap (Complete)
- 16/16 tickets completed and merged
- Foundation: repo, FastAPI, React shell, crawler pipeline
- All PRs merged to `dev`

#### Sprint 2 Recap (Partial → Completed in Sprint 3)
- **FE-06:** Completed by Evan Weber (June 25)
- **BE-06, BE-07:** Completed by PM due to reassignment
- Team reassignment documented

#### Sprint 3 Status (Current)
- Local work pushed and merged
- Integration testing complete
- Documentation updated

**Discussion:**
- What went well?
- What needs improvement?
- Lessons learned from the reassignment situation

---

### 3. Live Demo (20 min)

**Demonstrate:**
1. Splash screen and app loading
2. Ask a sample question about McNeese
3. Show citations and source links
4. Demonstrate conversation history
5. Show pipeline statistics (`/ask/stats`)
6. View query logs

**Test questions for demo:**
- "What are the admission deadlines?"
- "How do I apply for financial aid?"
- "What programs does McNeese offer?"

---

### 4. Technical Architecture Review (15 min)

**Backend:**
- FastAPI with `/health` and `/ask` endpoints
- ChromaDB for vector storage
- Claude Sonnet 4 for answer generation
- Query logging to JSONL

**Frontend:**
- React + TypeScript + Tailwind
- Framer Motion animations
- Design system with CSS variables
- Conversation persistence

**Integration:**
- SSE streaming for real-time responses
- Error handling and fallbacks

---

### 5. Sprint 4 Planning (40 min)

#### Proposed Sprint 4 Scope

| Ticket | Task | Proposed Owner |
|--------|------|----------------|
| S4-01 | Expand crawler to 15+ approved sources | PM |
| S4-02 | Add user feedback (thumbs up/down) | TBD |
| S4-03 | Admin statistics dashboard | TBD |
| S4-04 | Prepare for deployment | PM |
| S4-05 | Write user documentation | Content |
| S4-06 | Performance optimization | TBD |

**Discussion items:**
- Deployment target (Vercel? Railway? McNeese servers?)
- Need for user authentication?
- Priority of feedback vs admin dashboard
- Timeline for public beta

---

### 6. Role Assignments (15 min)

**Current assignments:**
- PM (Prince): Backend + Frontend + Coordination
- Evan Weber: Frontend support
- Content: Source registry management
- DevOps/QA: Testing and CI

**For Sprint 4:**
- Who takes which tickets?
- Any new team members?
- Landon's status?

---

### 7. Action Items & Next Steps (10 min)

**Capture:**
- Who does what by when
- Next meeting date
- Communication plan

---

### 8. Q&A and Open Discussion (5 min)

- Any concerns not addressed?
- Feedback on meeting format?

---

## Pre-Meeting Checklist (PM)

Before the meeting:
- [ ] All Sprint 3 work merged to `dev`
- [ ] Backend and frontend running locally for demo
- [ ] ChromaDB populated with test data
- [ ] Meeting room booked (Drew Hall)
- [ ] Laptop + projector ready
- [ ] This agenda shared with team

---

## Attendees

| Name | Role | Status |
|------|------|--------|
| Prince Pudasaini | PM | Confirmed |
| Evan Weber | Frontend | TBD |
| [Content Lead] | Content | TBD |
| [QA Lead] | DevOps/QA | TBD |

---

## Notes Section

*(To be filled during meeting)*

### Decisions Made:


### Action Items:

| Item | Owner | Due Date |
|------|-------|----------|
| | | |

### Parking Lot (for future discussion):


---

*Meeting duration: 2 hours with 10-minute buffer*
