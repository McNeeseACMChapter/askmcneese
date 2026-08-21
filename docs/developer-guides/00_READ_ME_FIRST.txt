ASKMCNEESE DEVELOPER GUIDES — COMPLETE SYSTEM DOCUMENTATION
Date: 2026-08-16
Branch: dev
Current commit: fddcb13
Project: ACM @ McNeese State University (NOT an official McNeese product)
Audience: New developers, team members, project maintainers

================================================================================
WHAT THIS DOCUMENTATION IS
================================================================================

This folder contains complete, truthful documentation for the AskMcNeese 
project as it exists right now. These guides are written for anyone who needs
to understand, maintain, or extend this system—whether you're a developer,
a project manager, or a new team member.

KEY FACTS:
- AskMcNeese is an ACM (Association for Computing Machinery) student project
- It is NOT an official McNeese State University product
- It is designed to help students find campus information and plan class schedules
- The system uses official McNeese sources but is independently developed

================================================================================
WHAT ASKMCNEESE DOES (PLAIN LANGUAGE)
================================================================================

AskMcNeese lets you ask questions about McNeese State University in your own
words. Instead of searching through multiple websites or clicking through menus,
you type a question like:

  "What calculus courses are offered in Fall 2026?"
  "When is the last day to drop a class?"
  "Where is the financial aid office?"

The system:
1. Understands what you're asking
2. Searches official McNeese sources (websites, Class Search database, calendars)
3. Finds relevant information
4. Gives you an answer with links to the original sources

It also includes a Class Planner that helps you:
- Search for Fall 2026 courses
- Check if courses conflict with each other
- Build a potential schedule
- See course details (time, instructor, CRN, seats available)

================================================================================
WHAT ASKMCNEESE CANNOT DO
================================================================================

This system does NOT:
- Register you for classes (that still happens in Banner)
- Access your student records or grades
- Make decisions for the university
- Replace official university websites or systems
- Answer questions that aren't in official McNeese sources
- Guarantee real-time seat counts (data is refreshed periodically)

================================================================================
PROJECT STRUCTURE (HOW THE FOLDERS WORK TOGETHER)
================================================================================

Think of AskMcNeese as having four main parts:

1. BACKEND (backend/) — The "brain" 
   - Receives your question
   - Searches for answers in databases and websites
   - Decides what information is relevant
   - Sends back the answer

2. FRONTEND (frontend/) — The "face"
   - The website you see and interact with
   - Chat interface where you type questions
   - Class Planner where you search courses
   - Settings, about pages, etc.

3. CRAWLER (crawler/) — The "librarian"
   - Runs offline (not when you ask questions)
   - Reads McNeese websites and saves important information
   - Updates the searchable database of campus content

4. KNOWLEDGE (knowledge/) — The "rulebook"
   - Configuration files that define what questions the system can handle
   - Lists of official McNeese sources
   - Rules for how to find and verify information

There are also supporting folders:
- ACM (acm/) — Separate ACM chapter management tool (not part of Ask)
- DOCS (docs/) — Documentation like these guides
- SCRIPTS (scripts/) — Utility programs for maintenance
- TESTS (tests/ and others) — Code that verifies everything works correctly

================================================================================
READING ORDER
================================================================================

Start here, then read these guides in order:

1.  00_READ_ME_FIRST.txt          ← You are here
2.  01_ROOT.txt                   Repository structure, environment setup
3.  02_BACKEND.txt                How questions get answered
4.  03_FRONTEND.txt               How the website works
5.  04_CRAWLER.txt                How campus content is indexed
6.  05_KNOWLEDGE.txt              Configuration and data sources
7.  06_ACM.txt                    Separate ACM chapter tool
8.  07_DOCS.txt                   Other documentation
9.  08_SCRIPTS.txt                Utility tools
10. 09_TESTS.txt                  Testing infrastructure
11. 10_GITHUB.txt                 Automated processes and deployment
12. 11_READY_TO_DELETE.txt        Files that are no longer needed
13. 12_COMPLETE_SYSTEM_NARRATION.txt   Full system overview (read last)

================================================================================
HOW TO USE THIS DOCUMENTATION
================================================================================

IF YOU WANT TO:

→ Understand how the whole system works
  Read: 00_READ_ME_FIRST.txt, then 12_COMPLETE_SYSTEM_NARRATION.txt

→ Change how questions are answered
  Read: 02_BACKEND.txt, then 05_KNOWLEDGE.txt

→ Change the website appearance or behavior
  Read: 03_FRONTEND.txt

→ Add new campus content to search
  Read: 04_CRAWLER.txt, then 05_KNOWLEDGE.txt

→ Change what questions the system recognizes
  Read: 05_KNOWLEDGE.txt, then 02_BACKEND.txt

→ Set up the project on your computer
  Read: 01_ROOT.txt, then 02_BACKEND.txt and 03_FRONTEND.txt

→ Deploy or host the project
  Read: 10_GITHUB.txt, then 01_ROOT.txt

================================================================================
WHEN DOCUMENTS CONFLICT
================================================================================

If different documents say different things, trust them in this order:

1. The actual code that's running (files in backend/, frontend/, etc.)
2. The test files (they show what the code is supposed to do)
3. These developer guides (docs/developer-guides/)
4. The system audit (docs/CURSOR_SYSTEM_TRUTH_AUDIT_2026-08-15/)
5. Older documentation files

If a guide says something that contradicts the code, the code is correct
and the guide needs to be updated.

================================================================================
LOCAL DEVELOPMENT SETUP (QUICK START)
================================================================================

When you run AskMcNeese locally, these are the correct addresses:

  Ask website:      http://127.0.0.1:5173
  Ask API:          http://127.0.0.1:8003
  ACM website:      http://127.0.0.1:3100
  ACM API:          http://127.0.0.1:3101

NOTE: Some old comments mention port 8000 for the API. That's outdated.
The current development setup uses port 8003.

DO NOT:
- Start the crawler when handling Ask requests (it runs separately)
- Confuse ACM ports with Ask ports
- Assume port 8000 is correct unless you specifically configured it

================================================================================
HOW THE SYSTEM ANSWERS A QUESTION (SIMPLE VERSION)
================================================================================

When you type a question and click send:

1. FRONTEND sends your question to BACKEND via the API
   - Only sends conversation history if it's a follow-up question
   - Default setting is "Adaptive" (search official sources + index)

2. BACKEND processes your question:
   a. Understands what domain/topic (registration, financial aid, etc.)
   b. Identifies what kind of answer you need (a date, a list, a process)
   c. Decides where to look (database, live websites, Class Search)

3. BACKEND searches for information:
   - ChromaDB: Indexed campus content (from crawler)
   - Class Search database: Fall 2026 courses and schedules
   - Live official pages: Current McNeese websites
   - Curated records: Calendar dates, service contacts

4. BACKEND evaluates what it found:
   - Does it answer the required parts of the question?
   - Is it from an approved source?
   - Is it recent enough to be trustworthy?

5. BACKEND generates an answer:
   - Uses Claude AI to write a clear response
   - Includes citations (links to sources)
   - Marks answer as complete, partial, or blocked

6. FRONTEND displays the answer:
   - Shows the response with citations
   - Displays "Learn more" links
   - For Class Planner results, shows course cards

The CRAWLER runs separately (not during questions) to keep the database fresh.
The KNOWLEDGE folder defines what questions we support and where to find answers.

================================================================================
IMPORTANT TRUTHS FOR NEW DEVELOPERS
================================================================================

1. ATTRIBUTION
   - This is an ACM student project, not official McNeese software
   - Always be clear about this distinction in documentation and UI

2. DATA FRESHNESS
   - Class Search data is refreshed periodically, not real-time
   - Seat counts may not match current Banner availability
   - Calendar dates come from curated records or official pages

3. CAPABILITIES
   - The system can only answer questions about topics in the knowledge folder
   - Having a "domain pack" doesn't mean we have comprehensive answers
   - Some questions will get "I don't have verified information" responses

4. SOURCES
   - Only uses official McNeese sources (websites, Class Search)
   - Does not scrape or use unofficial information
   - Does not access protected student data or Banner directly

5. ARCHITECTURE DECISIONS
   - Crawler runs offline to avoid slowing down question responses
   - Conversation history only sent for true follow-ups
   - Class Planner is planning only, not registration

================================================================================
PROJECT MAINTENANCE
================================================================================

REGULAR UPDATES NEEDED:
- Class Search data refresh (when McNeese updates course schedules)
- Crawler re-runs (when significant campus content changes)
- Academic calendar updates (each semester)
- Domain pack updates (when new question types are supported)

MONITORING:
- Health endpoint: /health (backend)
- Query logs: backend/logs/query_logs.jsonl (local)
- Test suites: backend/tests/ and frontend/src/*.test.ts(x)

================================================================================
GETTING HELP
================================================================================

When something is unclear:

1. Check the specific folder guide (02_BACKEND.txt, 03_FRONTEND.txt, etc.)
2. Read the complete system narration (12_COMPLETE_SYSTEM_NARRATION.txt)
3. Look at the actual code in that folder
4. Check test files for examples of how things should work
5. Search for keywords in docs/CURSOR_SYSTEM_TRUTH_AUDIT_2026-08-15/

Remember: The code is the ultimate truth. If documentation conflicts with
working code, trust the code and update the documentation.

================================================================================
NEXT STEPS
================================================================================

→ New to the project? Read 01_ROOT.txt next to set up your environment
→ Want the big picture? Jump to 12_COMPLETE_SYSTEM_NARRATION.txt
→ Need to make specific changes? Find your folder in the reading order above

Each guide includes:
- Purpose and scope
- Key files and their roles  
- How to make common changes
- What NOT to do (common mistakes)
- How it connects to other parts
