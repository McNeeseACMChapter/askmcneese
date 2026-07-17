export type UpdateCategory = "Product" | "Engineering" | "Design" | "Reliability" | "Release";
export type UpdateStatus = "shipped" | "in-progress" | "planned";

export interface UpdateItem {
  slug: string;
  title: string;
  summary: string;
  date: string;
  category: UpdateCategory;
  status: UpdateStatus;
  body: string;
  relatedDocs?: string[];
}

export const updates: UpdateItem[] = [
  {
    slug: "core-stabilization-pass-1",
    title: "Core Stabilization Pass 1",
    summary:
      "First stabilization pass made the public Ask flow truthful and more reliable across streaming, citations, activity narration, and error handling.",
    date: "2026-07-12",
    category: "Release",
    status: "shipped",
    body: `Pass 1 focused on making the public Ask experience dependable end to end. Citation identity now uses normalized URLs, Ask failures surface as one safe error card, activity fallbacks match backend wording, and documentation reflects the real RAG plus SSE pipeline.

Streaming answers render into one provisional assistant bubble that is replaced by a single final structured answer without per-token localStorage writes. Automated test suites pass across frontend and backend unit coverage.

Runtime validation is partially complete: scroll padding was added for sticky header overlap, while manual browser zoom, mobile keyboard, and mid-stream network interruption checks remain deferred.`,
    relatedDocs: [
      "docs/core-stabilization-change-log.md",
      "docs/core-stabilization-runtime-validation.md",
    ],
  },
  {
    slug: "sse-streaming-answer-rendering",
    title: "SSE Streaming Answer Rendering",
    summary:
      "Progressive answer chunks now render in a provisional assistant message and settle into one persisted structured answer.",
    date: "2026-07-12",
    category: "Engineering",
    status: "shipped",
    body: `Before this work, onStreamUpdate was unused and the full answer appeared at once. The Ask flow now maintains a transient provisional message per request and conversation, streams progressive markdown body text only, and persists the final structured answer once.

Stale callbacks are ignored and abort clears the provisional bubble. askSession helpers coordinate merge behavior so duplicate assistant responses do not appear. SemanticAnswer supports streaming mode while structured sections wait for completion.`,
    relatedDocs: ["docs/core-stabilization-change-log.md"],
  },
  {
    slug: "citation-url-dedupe",
    title: "Citation URL Deduplication",
    summary:
      "Citations dedupe by normalized URL so distinct sources with similar titles are preserved and trailing-slash duplicates collapse.",
    date: "2026-07-12",
    category: "Reliability",
    status: "shipped",
    body: `Citation grouping previously deduplicated by lowercase title, which could drop distinct URLs that shared a page name. The primary key is now a normalized URL: same title with different URLs both remain visible, trailing-slash duplicates collapse, and malformed URLs no longer crash the UI.

Seven unit tests cover the new behavior in CitationGroup. Query-parameter canonicalization beyond URL parsing is not yet applied.`,
    relatedDocs: ["docs/core-stabilization-change-log.md"],
  },
  {
    slug: "activity-narration-alignment",
    title: "Activity Narration Alignment",
    summary:
      "Frontend activity fallbacks and typing-indicator copy now match backend activity_events.py wording.",
    date: "2026-07-12",
    category: "Product",
    status: "shipped",
    body: `Live Answer Progress depends on consistent narration between backend events and frontend fallbacks. Previously, frontend SAFE_MESSAGES drifted from backend strings such as preparing-your-answer copy.

Frontend fallbacks now mirror backend activity_events.py. The backend message is preferred when safe, and TypingIndicator early copy is aligned. The backend still does not emit every defined event key, which remains a known limitation.`,
    relatedDocs: ["docs/core-stabilization-change-log.md"],
  },
  {
    slug: "ask-error-surfacing",
    title: "Ask Error Surfacing",
    summary:
      "Non-abort failures show one assistant error card; user abort clears provisional state without an error message.",
    date: "2026-07-12",
    category: "Reliability",
    status: "shipped",
    body: `Ask failures could previously leave a user message without a clear assistant response, and abort error clearing was incomplete. Non-abort failures now produce one isError assistant message. Abort returns null with error cleared and provisional stream removed while loading ends.

Hook and askSession merge tests cover fetch rejection, HTTP 500, abort, and stale error clearing. End-to-end App mount coverage was deferred as heavy; contract behavior is covered via hook and helper tests.`,
    relatedDocs: ["docs/core-stabilization-change-log.md"],
  },
  {
    slug: "visual-system-overhaul",
    title: "Visual System Overhaul",
    summary:
      "Typography, glass surfaces, public routes, and McNeese brand colors bring the chat app closer to a finished campus product.",
    date: "2026-07-12",
    category: "Design",
    status: "in-progress",
    body: `The visual overhaul introduces EB Garamond for editorial headings, Source Sans 3 for interface text, three glass surface levels, semantic color roles, and responsive page gutters. Public routes for About, Updates, Status, Settings, and Feedback support deep linking and browser history.

About and Updates pages document the project story and real milestones. Mobile navigation consolidates primary routes into four items. Live Answer Progress, expanded answer presentation, and contextual sidebars continue rolling out alongside this pass.`,
    relatedDocs: [
      "docs/visual-overhaul-map.md",
      "docs/UI_OVERHAUL_AUDIT.md",
    ],
  },
];

export const featuredUpdateSlug = "core-stabilization-pass-1";
