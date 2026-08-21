import { useEffect, useMemo } from "react";
import { LiveAnswerProgress } from "../components/chat/LiveAnswerProgress";
import { ChatBubble } from "../components/chat/ChatBubble";
import { CitationGroup } from "../components/chat/CitationGroup";
import { MessageActions } from "../components/chat/MessageActions";
import { applyActivityEvent, completeAskRun, createAskRun } from "../lib/askRun";
import type { ActivityEvent, ChatMessage } from "../types";

const user: ChatMessage = {
  id: "u1",
  role: "user",
  text: "What are the undergraduate admissions deadlines?",
  timestamp: new Date(),
};

const assistantText =
  "Undergraduate applications are submitted through the McNeese admissions portal. Verify deadlines on the official admissions pages before you apply.";

const citations = [
  {
    id: "c1",
    title: "McNeese Admissions — Application Requirements",
    url: "https://www.mcneese.edu/admissions",
  },
  {
    id: "c2",
    title: "Academic Calendar — Important Dates",
    url: "https://www.mcneese.edu/calendar",
  },
];

export function VisualProgressFixture({ mode: modeProp }: { mode?: string } = {}) {
  const mode =
    modeProp ??
    new URLSearchParams(typeof window !== "undefined" ? window.location.search : "").get("mode") ??
    "active";

  const run = useMemo(() => {
    let next = createAskRun({
      runId: "viz-run",
      requestId: "viz",
      turnId: "viz-turn",
      userMessageId: "u1",
      assistantMessageId: "a1",
    });
    const events: ActivityEvent[] = [
      {
        requestId: "viz",
        runId: "viz-run",
        event: "request.accepted",
        message: "Starting your request",
        elapsedMs: 180,
        metadata: { phase: "understand", kind: "milestone" },
      },
      {
        requestId: "viz",
        runId: "viz-run",
        event: "query.analyzing",
        message: "Understanding what you need",
        elapsedMs: 420,
        metadata: { phase: "understand", kind: "milestone" },
      },
      {
        requestId: "viz",
        runId: "viz-run",
        event: "skill.started",
        message: "Searching official McNeese websites",
        elapsedMs: 900,
        metadata: {
          phase: "search",
          kind: "operation",
          operation_id: "official-web",
          skill: "official_web",
          operation_label: "Official McNeese websites",
        },
      },
      {
        requestId: "viz",
        runId: "viz-run",
        event: "retrieval.source_found",
        message: "Reading a relevant source",
        elapsedMs: 1400,
        metadata: {
          phase: "search",
          kind: "evidence",
          source_title: "Academic Calendar 2026–27",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/calendar",
          source_type: "official",
          operation_id: "official-web",
        },
      },
      {
        requestId: "viz",
        runId: "viz-run",
        event: "retrieval.completed",
        message: "Collected the relevant sources",
        elapsedMs: 2100,
        metadata: { sources_found: 3, phase: "search", kind: "milestone" },
      },
      {
        requestId: "viz",
        runId: "viz-run",
        event: "answer.generating",
        message: "Writing your answer",
        elapsedMs: 2700,
        metadata: { phase: "compose", kind: "milestone" },
      },
    ];
    for (const item of events) {
      next = applyActivityEvent(next, item);
    }
    if (mode === "complete") return completeAskRun(next, "completed");
    return { ...next, status: "streaming" as const };
  }, [mode]);

  useEffect(() => {
    if (mode !== "complete") return;
    const id = window.setTimeout(() => {
      const button = Array.from(document.querySelectorAll("button")).find((el) =>
        (el.textContent ?? "").includes("Sources ·"),
      );
      button?.click();
    }, 250);
    return () => window.clearTimeout(id);
  }, [mode]);

  return (
    <main className="mx-auto w-full max-w-chat px-[var(--page-gutter)] py-8">
      <div className="chatMessageStack">
        <ChatBubble message={user} />
        <LiveAnswerProgress run={run} />
        {mode !== "active" && (
          <div>
            <p className="mb-2 font-sans text-sm font-semibold">AskMcNeese</p>
            <p className="font-sans text-[17px] leading-[1.62] text-text-primary">{assistantText}</p>
            <div className="mt-8">
              <CitationGroup citations={citations} />
            </div>
            <MessageActions text={assistantText} />
          </div>
        )}
      </div>
    </main>
  );
}
