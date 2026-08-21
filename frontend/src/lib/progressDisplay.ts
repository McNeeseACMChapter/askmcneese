/**
 * Turn raw SSE activity events into display rows for live progress.
 * Prefers the server's layman message so each terminal step stays visible.
 */
import type { ActivityEvent } from "../types";

export type ProgressPhaseId =
  | "request"
  | "understanding"
  | "search"
  | "selection"
  | "citations"
  | "preparation"
  | "completion"
  | "other";

export interface DisplayPhase {
  id: ProgressPhaseId;
  message: string;
  elapsedMs?: number;
  eventKeys: string[];
}

function phaseForEvent(event: string): ProgressPhaseId {
  if (event.startsWith("request.") && event !== "request.failed") return "request";
  if (event.startsWith("query.")) return "understanding";
  if (event.startsWith("retrieval.") || event === "reranking.started") return "search";
  if (event.startsWith("reranking.") || event === "retrieval.source_found") return "selection";
  if (event.startsWith("citations.")) return "citations";
  if (event.startsWith("answer.") && event !== "answer.completed") return "preparation";
  if (event === "answer.completed" || event === "request.failed") return "completion";
  return "other";
}

/** Keep each meaningful server message as its own row (no generic phase overwrite). */
export function groupActivityPhases(events: ActivityEvent[]): DisplayPhase[] {
  const rows: DisplayPhase[] = [];
  let lastMessage = "";

  for (const event of events) {
    const message = (event.message || "").trim();
    if (!message) continue;
    // Collapse only exact consecutive duplicates
    if (message === lastMessage) {
      const prev = rows[rows.length - 1];
      if (prev) {
        prev.eventKeys.push(event.event);
        if (event.elapsedMs !== undefined) prev.elapsedMs = event.elapsedMs;
      }
      continue;
    }
    lastMessage = message;
    rows.push({
      id: phaseForEvent(event.event),
      message,
      elapsedMs: event.elapsedMs,
      eventKeys: [event.event],
    });
  }

  return rows;
}

export function formatElapsed(ms?: number): string | null {
  if (ms === undefined || ms < 100) return null;
  if (ms < 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function sourcesFromActivity(events: ActivityEvent[]): number | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const meta = events[i]?.metadata;
    if (!meta) continue;
    const value = meta.sources_found ?? meta.num_results;
    if (typeof value === "number") return value;
  }
  return null;
}
