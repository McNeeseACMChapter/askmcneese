import type { DevelopmentChapter, UpdateArea } from "./types";
import { CHAPTER_TICKETS } from "./parseTimeline";

function chapter(
  partial: Omit<DevelopmentChapter, "ticketIds"> & { id: keyof typeof CHAPTER_TICKETS | string },
): DevelopmentChapter {
  return {
    ...partial,
    ticketIds: CHAPTER_TICKETS[partial.id],
  };
}

export const DEVELOPMENT_CHAPTERS: DevelopmentChapter[] = [
  chapter({
    id: "project-origin",
    number: 1,
    title: "From idea to project",
    dateLabel: "MAR 25 — APR 29, 2026",
    startDate: "2026-03-25",
    endDate: "2026-04-29",
    summary: "Project ownership and ACM approval came before any implementation.",
    situation:
      "AskMcNeese did not begin as a repository. It began as an ACM chapter decision about who would own a summer project.",
    decision:
      "The AskMcNeese team started with organization: elect a project manager, then propose a campus information system to the chapter.",
    expectedResult:
      "The project would have a named owner and chapter support before anyone wrote production code.",
    narrative:
      "On March 25, Prince Pudasaini was elected Project Manager during ACM chapter elections at Drew 317. On April 29, the summer project was proposed to ACM. The sequence is the point: the chapter established ownership and intent first.",
    outcome:
      "AskMcNeese existed as a chapter project with a project manager and a public proposal.",
    enabledNext: "Research whether the idea had enough direction to justify building.",
    changeFlow: ["ACM elections", "Project ownership", "Summer project proposal"],
    tags: ["Product", "ACM"],
  }),
  chapter({
    id: "research",
    number: 2,
    title: "Research before implementation",
    dateLabel: "MAY 23 — MAY 26, 2026",
    startDate: "2026-05-23",
    endDate: "2026-05-26",
    summary: "The project traded early coding speed for feasibility review and faculty guidance.",
    situation:
      "The proposal existed, but the team had not yet tested whether the concept could be built as a campus information system.",
    decision:
      "Pause implementation. Research feasibility, write the project documentation, and present it to faculty advisors.",
    expectedResult:
      "Clarify whether the concept had enough direction to justify forming a development team.",
    narrative:
      "On May 23 the project was researched and documented. On May 26 it was presented to Dr. Menon and Dr. Vasan over Microsoft Teams, then followed by a technical advising call with Dr. Menon. Faculty review happened before Sprint 1, not after a first prototype.",
    outcome:
      "The project had a reviewed direction and faculty technical guidance.",
    enabledNext: "Form the team and build a repository structure that could support parallel work.",
    changeFlow: ["Feasibility research", "Faculty presentation", "Technical advising"],
    tags: ["Product", "Docs"],
  }),
  chapter({
    id: "foundation",
    number: 3,
    title: "Building the foundation",
    dateLabel: "JUN 06 — JUN 15, 2026",
    startDate: "2026-06-06",
    endDate: "2026-06-15",
    summary: "Team structure, repository controls, Sprint 1, and the first proven system components.",
    situation:
      "The project had moved beyond proposal, but it still needed a code and responsibility structure that could support parallel work.",
    decision:
      "Separate responsibilities, establish the Git branch model, create the Sprint 1 structure, and prove each system layer.",
    expectedResult:
      "Developers should be able to work independently without turning the repository into one shared editing surface.",
    narrative:
      "June 6 established the team: Prince as Project Manager, Landon on Backend, Evan Weber on Frontend, with Content & Knowledge and DevOps/QA roles assigned. The repository, branch strategy, sprint backlog, and subdomains followed immediately. When the initial backend submission used Django instead of the planned FastAPI stack and did not include the crawler pipeline, a reference implementation was created so the project would not remain blocked. That reference proved crawler → clean → chunk → ChromaDB, a /health endpoint, the database schema, and a React + Vite + TypeScript + Tailwind frontend shell. CI on .github/workflows/ci.yml closed Sprint 1 at 16/16. A Playwright browser fallback was added for McNeese 403 and JavaScript-heavy pages.",
    outcome:
      "Sprint 1 finished with proven components, repository controls, and a working CI path.",
    enabledNext: "Connect those components through /ask.",
    changeFlow: [
      "Repository controls",
      "FastAPI foundation",
      "Crawler / ChromaDB",
      "Frontend shell",
      "CI",
    ],
    tags: ["Product", "Backend", "Frontend", "Crawler", "DevOps"],
  }),
  chapter({
    id: "ask-pipeline",
    number: 4,
    title: "Making /ask work",
    dateLabel: "JUN 19 — JUN 30, 2026",
    startDate: "2026-06-19",
    endDate: "2026-06-30",
    summary: "Sprint 1 had proven the parts. Sprint 2 connected them into a retrieval product.",
    situation:
      "The foundation existed as separate proven layers. A student still could not ask a question and receive a retrieved answer.",
    decision:
      "Give the frontend a design system, merge a working /ask RAG pipeline, and integrate that pipeline into the student-facing UI.",
    expectedResult:
      "A question could retrieve evidence, generate an answer, and stream it to the frontend.",
    narrative:
      "On June 19 the UI/UX Design System Architecture was written for the frontend team. On June 30, PR #14 merged feature/backend-ask: Claude, Server-Sent Events, query logging, and full RAG execution. The same day, PR #15 merged Evan Weber's frontend /ask integration, with design-system, Framer Motion, conversation history, and splash-screen work added on top. Backend responsibility was then formally reassigned so Sprint 3 would not wait on an undelivered path. Evan's on-time frontend delivery (commit 792ed5c on June 25) stayed in the record.",
    outcome:
      "/ask became an integrated system instead of a collection of Sprint 1 components.",
    enabledNext: "Make retrieval more reliable than a first working pipeline.",
    changeFlow: ["Design system", "/ask RAG pipeline", "Frontend integration", "Team reassignment"],
    tags: ["Frontend", "Backend", "Retrieval"],
    turningPoint: true,
  }),
  chapter({
    id: "retrieval-reliability",
    number: 5,
    title: "Making retrieval more reliable",
    dateLabel: "JUL 01 — JUL 10, 2026",
    startDate: "2026-07-01",
    endDate: "2026-07-10",
    summary: "Working RAG was not enough. The system needed governed sources, broader documents, and tests.",
    situation:
      "/ask could answer, but the evidence set, routing, and regression protection were still thin.",
    decision:
      "Expand what the crawler could read, improve query routing, and lock behavior behind offline unit tests in CI.",
    expectedResult:
      "Answers would come from a wider, more deliberate evidence set, and retrieval changes would fail in CI before they failed in use.",
    narrative:
      "PDF ingestion with PyPDF2 opened course catalogs and policy documents. Intent classification, persona detection, query expansion, and reranking were added to the /ask path. Streaming and citation rendering were refined. Offline unit tests entered CI. source_registry_merged.csv was marked as the authoritative registry. An ingest audit counted 1,328 indexed chunks and made coverage gaps visible enough to plan the next sprint.",
    outcome:
      "Retrieval had governed sources, document breadth, and repeatable tests.",
    enabledNext: "Treat Ask as an orchestrated product rather than a single RAG call.",
    changeFlow: [
      "PDF ingestion",
      "Query routing",
      "CI tests",
      "source_registry_merged.csv",
      "1,328-chunk audit",
    ],
    tags: ["Retrieval", "Crawler", "Knowledge", "QA"],
  }),
  chapter({
    id: "rccs",
    number: 6,
    title: "From RAG to a governed system",
    dateLabel: "JUL 11 — JUL 17, 2026",
    startDate: "2026-07-11",
    endDate: "2026-07-17",
    summary: "RCCS turned retrieval into an orchestrated product with a shared visual system.",
    situation:
      "Retrieval quality was improving, but the product still behaved like a pipeline with a chat skin.",
    decision:
      "Introduce RCCS — Retrieval, Classification, Context, Synthesis — and rebuild the public shell around honest capabilities and one token source.",
    expectedResult:
      "Ask would route work through named stages, tell the truth about what it can do, and look like one campus product.",
    narrative:
      "The chat UI moved to semantic answers, activity indicators, and About / Status / Settings / Feedback routes. RCCS landed on July 12 with companion search and feature flags. Knowledge versus web modes were made honest. Optional Perplexity research and a supervisor path were added, defaulting off. Core stabilization covered streaming, citations, and errors. The Hard Stoppage architecture document captured the system for stakeholders. A v0.5.0 baseline was pushed in ten clean commits. variables.css became the design-system source of truth, with McNeese Midnight Blue #002F87 and Sunflower Gold #FFCE00 as identity anchors.",
    outcome:
      "AskMcNeese started behaving like a governed product with a stable visual contract.",
    enabledNext: "Widen retrieval coverage without dropping the governance that RCCS introduced.",
    changeFlow: ["Semantic answer UI", "RCCS", "Capability honesty", "v0.5.0", "variables.css"],
    tags: ["Retrieval", "Frontend", "Backend"],
    turningPoint: true,
  }),
  chapter({
    id: "governance",
    number: 7,
    title: "Wider retrieval and system governance",
    dateLabel: "JUL 18 — JUL 28, 2026",
    startDate: "2026-07-18",
    endDate: "2026-07-28",
    summary: "Coverage grew, and governance grew with it — including a separate ACM chapter system.",
    situation:
      "RCCS could orchestrate an answer, but campus coverage was still narrow, and the repository was also carrying ACM chapter-operations work.",
    decision:
      "Expand companion sources and page-level retrieval, and design ACM chapter governance in the same repository without folding it into Ask.",
    expectedResult:
      "More campus questions would resolve from opened pages, and ACM would have a proposed operating path of its own.",
    narrative:
      "Companion sources expanded to social and organization surfaces. Hybrid retrieval gained deduplication, timeout handling, and a keep-finished rule. A Presence.io adapter added a fast path for organization questions. In parallel, the team scaffolded the ACM program under askmcneese/acm/, proposed GOV-001 through GOV-020, and built an ACM Panel visual foundation — 7/7 tests and 24 screenshots — that shares design DNA with AskMcNeese but not its database, API, accounts, or retrieval logic. Twenty-five campus-intelligence domain packs and opened-page retrieval replaced link dumping. .gitignore hardening kept secrets off GitHub.",
    outcome:
      "Ask coverage widened under retrieval rules, while ACM Panel remained a separate chapter-management system.",
    enabledNext: "Prepare a closed beta that visitors — not only developers — could depend on.",
    changeFlow: [
      "Companion sources",
      "Opened-page retrieval",
      "25 domain packs",
      "ACM Panel (separate)",
      ".gitignore hardening",
    ],
    tags: ["Retrieval", "Knowledge", "ACM", "DevOps"],
  }),
  chapter({
    id: "closed-beta",
    number: 8,
    title: "Preparing for closed beta",
    dateLabel: "AUG 01 — AUG 08, 2026",
    startDate: "2026-08-01",
    endDate: "2026-08-08",
    summary: "The question shifted from whether developers could use it to whether beta visitors could depend on it.",
    situation:
      "The system worked in development. A guest still needed a first-run experience that stayed readable, honest, and stable.",
    decision:
      "Stabilize adaptive source modes, mobile reading, guest onboarding, and the public product shell for closed beta.",
    expectedResult:
      "A visitor could ask a question, see live activity, and trust that the product would behave the same way on a phone.",
    narrative:
      "Adaptive source modes and a live activity trail landed in the Ask UI. The crawler was aligned with the governed registry. ACM Panel module work continued alongside Ask, not inside it. Public brand and architecture documentation caught up with the running product. Tests locked routing, page-read, and dedupe behavior. CI kept running while Chroma had no patched HTTP-server release. Taxonomy-generated search phrases let lean deploys skip a 50k local query corpus. Mobile readability, navigation, and PWA corrections landed in the same week. August 8 closed the Beta Version Sprint and a stability pass for guest onboarding, conversation-thread separation, and research-mode clarification.",
    outcome:
      "Closed beta had a connected Ask experience, not only a working retrieval path.",
    enabledNext: "Put Class Planner on production data that can survive deployment.",
    changeFlow: [
      "Adaptive source modes",
      "Live activity trail",
      "Mobile readability",
      "Beta Version Sprint",
      "Guest onboarding",
    ],
    tags: ["Frontend", "Product", "QA", "DevOps"],
    turningPoint: true,
  }),
  chapter({
    id: "class-planner-production",
    number: 9,
    title: "Putting Class Planner on production data",
    dateLabel: "AUG 09 — AUG 10, 2026",
    startDate: "2026-08-09",
    endDate: "2026-08-10",
    summary: "Class Planner moved from a feature with data to a production data system.",
    situation:
      "Class Planner could search classes, but the dataset could not survive production the way a campus tool needs to.",
    decision:
      "Move live schedules to PostgreSQL, protect synchronization, and publish availability atomically.",
    expectedResult:
      "Users should see either the previous complete dataset or the new complete dataset — never a partially synchronized state.",
    narrative:
      "August 9 gave Class Planner a PostgreSQL backbone, protected sync, availability refresh, and a documented Render path. Frontend work loaded sections on demand and repaired schedule-display gaps. August 10 bootstrapped the validated Fall 2026 dataset for term 202660 — 1,606 sections — onto production, wired the live PostgreSQL API, and recovered empty datasets automatically. The free Render tier required Alembic migrations at build time, because free web services do not support pre-deploy commands. Parallel subject fetching, abandoned-lock recovery, and one bulk availability transaction made the first production import reliable.",
    outcome:
      "Class Planner published a complete Fall 2026 dataset instead of a demo or a partial sync.",
    enabledNext: "Spend the next days on answer correctness rather than data plumbing.",
    changeFlow: [
      "Local Class Search",
      "PostgreSQL",
      "Protected synchronization",
      "Atomic publication",
      "1,606-section Fall 2026 dataset",
    ],
    tags: ["Class Planner", "Backend", "DevOps"],
  }),
  chapter({
    id: "grounding",
    number: 10,
    title: "Grounding and correctness",
    dateLabel: "AUG 11 — AUG 16, 2026",
    startDate: "2026-08-11",
    endDate: "2026-08-16",
    summary: "Correctness required restoring the actual user question as the primary control signal.",
    situation:
      "More routing logic had accumulated. Some answers were being steered by leftover FAQ-style paths and conversation glue instead of the question a student just asked.",
    decision:
      "Ground answers in official pages and Class Search, finish the mobile and guest experience, and remove routing that replaced the current question.",
    expectedResult:
      "Questions such as calculus offerings would resolve from official listings, not stale routing.",
    narrative:
      "Guest identity became durable in the browser. Mobile work reached a completion milestone. Grounding and follow-up handling improved in commit 2f75921, with Ziyan collaborating. On August 16, commit fddcb13 stopped leftover FAQ-style routing, conversation-glue contamination, and destination stubs from replacing official page reads and Class Search term listings. The calculus routing regression was the visible proof that the actual question had to remain in charge.",
    outcome:
      "Ask returned to the student's current question, with official pages and Class Search as the evidence path.",
    enabledNext: "After a team transition, write the system down so the project could continue without depending on memory.",
    changeFlow: [
      "Durable guest identity",
      "Mobile completion",
      "Evidence grounding",
      "fddcb13",
      "Official page and Class Search reads",
    ],
    tags: ["Retrieval", "Frontend", "Backend"],
    turningPoint: true,
  }),
  chapter({
    id: "transition",
    number: 11,
    title: "Making the project transferable",
    dateLabel: "AUG 16 — AUG 20, 2026",
    startDate: "2026-08-16",
    endDate: "2026-08-20",
    summary: "After the team transition, documentation became part of engineering continuity.",
    situation:
      "On August 16, Ziyan departed. Project knowledge could no longer live only in individual memory.",
    decision:
      "Document the running system, reconstruct the timeline from repository history, and keep frontend ownership with Evan while Prince assumed the remaining engineering roles.",
    expectedResult:
      "A new developer should be able to understand AskMcNeese from the repository rather than from a handoff conversation.",
    narrative:
      "The recorded transition is factual, not a verdict: Ziyan left at the end of August 16; Evan Weber continued Frontend; Prince assumed Project Manager, Backend, Crawler, Knowledge, DevOps, Docs, Tests, and ACM responsibilities. That evening produced 13 developer guides (00–12), 201,177 bytes, covering the system in plain language — including the explicit boundary that ACM Panel is not part of Ask retrieval. August 17 reconstructed uncommitted work, restored missing ticket 60, and compiled 28 commits from git history into the canonical timeline under a NO FAKE DATA rule. August 20 added an ACM-facing security documentation pack.",
    outcome:
      "The project record became complete enough to transfer — and complete enough to publish on this page.",
    enabledNext: "Maintain the canonical timeline as the source for this development story.",
    changeFlow: [
      "Team transition",
      "13 developer guides",
      "Timeline reconstruction",
      "NO FAKE DATA verification",
      "Security documentation pack",
    ],
    tags: ["Docs", "Product", "ACM"],
  }),
];

export const CHAPTER_BY_ID = Object.fromEntries(
  DEVELOPMENT_CHAPTERS.map((chapterItem) => [chapterItem.id, chapterItem]),
) as Record<string, DevelopmentChapter>;

export const LEGACY_HASH_ALIASES: Record<string, string> = {
  releases: "closed-beta",
  development: "foundation",
  limitations: "record-end",
};

export const PLANNED_DIRECTION = {
  title: "Canvas-connected course context",
  status: "planned" as const,
  detail:
    "Broader answer coverage comes first. Canvas-connected course context is a later direction and will require clear consent, privacy review, and secure McNeese access before it becomes available.",
};

export const AREA_FILTERS: Array<{ id: "All" | UpdateArea; label: string }> = [
  { id: "All", label: "All" },
  { id: "Product", label: "Product" },
  { id: "Frontend", label: "Frontend" },
  { id: "Backend", label: "Backend" },
  { id: "Retrieval", label: "Retrieval" },
  { id: "Knowledge", label: "Knowledge" },
  { id: "Crawler", label: "Crawler" },
  { id: "Class Planner", label: "Class Planner" },
  { id: "DevOps", label: "DevOps" },
  { id: "QA", label: "QA" },
  { id: "Docs", label: "Docs" },
  { id: "ACM", label: "ACM" },
];
