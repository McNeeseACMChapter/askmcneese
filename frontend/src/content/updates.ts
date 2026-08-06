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
    slug: "closed-beta-live-retrieval",
    title: "Closed beta: live campus answers",
    summary:
      "AskMcNeese now runs a public closed-beta API with hybrid retrieval — official McNeese pages, page reads, and adaptive modes — so answers cite real sources instead of dumping links.",
    date: "2026-08-05",
    category: "Release",
    status: "shipped",
    body: `The closed-beta backend is live with RCCS hybrid retrieval, page-open reading, structured answers, and search-provider fallbacks (Tavily, SerpAPI, Perplexity, DuckDuckGo). Adaptive, McNeese-only, and Include-the-web modes are available in the composer.

The frontend ships a calmer mobile Ask welcome, translucent chat history, Usage metrics, and SPA-safe hosting so refresh keeps the app alive. Knowledge-index depth on the free host is still thinner than a full campus crawl; live official pages carry most of the load.`,
  },
  {
    slug: "mobile-ask-readability",
    title: "Mobile Ask readability pass",
    summary:
      "Phone Ask drops heavy chrome and suggestions, keeps a warm greeting plus ask-in-your-own-words, and raises type so the page is easier to read on a handset.",
    date: "2026-08-05",
    category: "Design",
    status: "shipped",
    body: `Empty Ask on phones now centers a short greeting and the question prompt. Suggestion lists and trust footnotes are removed to cut cognitive load. Composer width and safe-area padding were tightened so the input no longer feels glued to the iOS URL bar.`,
  },
  {
    slug: "core-stabilization-pass-1",
    title: "Core Stabilization Pass 1",
    summary:
      "First stabilization pass made the public Ask flow truthful across streaming, citations, activity narration, and error handling.",
    date: "2026-07-12",
    category: "Release",
    status: "shipped",
    body: `Pass 1 focused on making the public Ask experience dependable end to end. Citation identity uses normalized URLs, Ask failures surface as one safe error card, activity fallbacks match backend wording, and streaming settles into one structured answer.`,
  },
  {
    slug: "sse-streaming-answer-rendering",
    title: "SSE Streaming Answer Rendering",
    summary:
      "Progressive answer chunks render in a provisional assistant message and settle into one persisted structured answer.",
    date: "2026-07-12",
    category: "Engineering",
    status: "shipped",
    body: `The Ask flow maintains a transient provisional message per request, streams progressive markdown, and persists the final structured answer once. Stale callbacks are ignored and abort clears the provisional bubble.`,
  },
  {
    slug: "citation-url-dedupe",
    title: "Citation URL Deduplication",
    summary:
      "Citations dedupe by normalized URL so distinct sources with similar titles are preserved.",
    date: "2026-07-12",
    category: "Reliability",
    status: "shipped",
    body: `The primary citation key is a normalized URL: same title with different URLs both remain visible, and trailing-slash duplicates collapse.`,
  },
  {
    slug: "visual-system-overhaul",
    title: "Visual System Overhaul",
    summary:
      "Typography, surfaces, public routes, and McNeese brand colors bring the chat app closer to a finished campus product.",
    date: "2026-07-12",
    category: "Design",
    status: "shipped",
    body: `Editorial and interface type, semantic color roles, and public routes for About, Updates, Usage, Settings, and Feedback support deep linking and a calmer campus shell.`,
  },
];

export const featuredUpdateSlug = "closed-beta-live-retrieval";
