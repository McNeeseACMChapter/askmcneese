/**
 * Ask run ownership — each live-activity panel belongs to one assistant message.
 */

import type { ActivityEvent } from "../types";

export type AskRunStatus =
  | "queued"
  | "running"
  | "streaming"
  | "completed"
  | "failed"
  | "cancelled";

export type LiveStageStatus = "active" | "completed" | "failed";

export interface LiveStage {
  id: string;
  event: string;
  label: string;
  detail?: string;
  status: LiveStageStatus;
  elapsedMs?: number;
  sequence: number;
}

export interface AskRun {
  runId: string;
  requestId: string;
  turnId: string;
  userMessageId: string;
  assistantMessageId: string;
  status: AskRunStatus;
  startedAt: number;
  completedAt?: number;
  stages: LiveStage[];
  processedEventKeys: string[];
  sourcesFound?: number;
}

export function createAskRun(input: {
  runId: string;
  requestId: string;
  turnId: string;
  userMessageId: string;
  assistantMessageId: string;
}): AskRun {
  return {
    ...input,
    status: "queued",
    startedAt: Date.now(),
    stages: [],
    processedEventKeys: [],
  };
}

function eventKey(event: ActivityEvent): string {
  return `${event.requestId}|${event.runId ?? ""}|${event.event}|${event.message}|${event.elapsedMs ?? ""}`;
}

/** Map a backend activity event onto run stages (deduped, ordered). */
export function applyActivityEvent(run: AskRun, event: ActivityEvent): AskRun {
  if (event.requestId && run.requestId && event.requestId !== run.requestId) {
    console.warn("Unknown AskMcNeese run/request", event.requestId, "expected", run.requestId);
    return run;
  }
  if (event.runId && event.runId !== run.runId) {
    console.warn("Unknown AskMcNeese run", event.runId, "expected", run.runId);
    return run;
  }

  const key = eventKey(event);
  if (run.processedEventKeys.includes(key)) return run;

  const sequence = run.stages.length;
  // Soft merge: identical consecutive message+event updates the active stage.
  const last = run.stages[run.stages.length - 1];
  if (last && last.event === event.event && last.label === event.message) {
    return {
      ...run,
      status: run.status === "queued" ? "running" : run.status,
      stages: run.stages.map((stage, index) =>
        index === run.stages.length - 1
          ? {
              ...stage,
              elapsedMs: event.elapsedMs ?? stage.elapsedMs,
              detail: detailFromMetadata(event) ?? stage.detail,
            }
          : stage,
      ),
      sourcesFound: sourcesFromEvent(event) ?? run.sourcesFound,
      processedEventKeys: [...run.processedEventKeys, key],
    };
  }

  const completedStages = run.stages.map((stage) =>
    stage.status === "active" ? { ...stage, status: "completed" as const } : stage,
  );

  const isTerminal =
    event.event === "answer.completed" ||
    event.event === "request.failed" ||
    event.event === "answer.failed";

  const nextStage: LiveStage = {
    id: `stg-${run.runId}-${sequence}`,
    event: event.event,
    label: event.message,
    detail: detailFromMetadata(event),
    status: isTerminal || event.event === "request.failed" ? "completed" : "active",
    elapsedMs: event.elapsedMs,
    sequence,
  };

  if (event.event === "request.failed") {
    nextStage.status = "failed";
  }

  let status: AskRunStatus = run.status === "queued" ? "running" : run.status;
  if (event.event.startsWith("answer.") && event.event !== "answer.completed") {
    status = "streaming";
  }
  if (event.event === "answer.completed") status = "completed";
  if (event.event === "request.failed") status = "failed";

  return {
    ...run,
    status,
    stages: [...completedStages, nextStage],
    processedEventKeys: [...run.processedEventKeys, key],
    sourcesFound: sourcesFromEvent(event) ?? run.sourcesFound,
    completedAt:
      status === "completed" || status === "failed" ? Date.now() : run.completedAt,
  };
}

export function completeAskRun(run: AskRun, status: AskRunStatus = "completed"): AskRun {
  return {
    ...run,
    status,
    completedAt: Date.now(),
    stages: run.stages.map((stage) =>
      stage.status === "active" ? { ...stage, status: "completed" as const } : stage,
    ),
  };
}

export function shouldShowLiveActivity(run: AskRun): boolean {
  if (run.status === "queued" || run.status === "running" || run.status === "streaming") {
    return true;
  }
  // Keep a compact completed summary attached to the turn.
  return run.stages.length > 0;
}

function detailFromMetadata(event: ActivityEvent): string | undefined {
  const meta = event.metadata;
  if (!meta) return undefined;
  // Prefer concrete source titles when present — that's the realtime signal.
  if (typeof meta.source_preview === "string" && meta.source_preview.trim()) {
    return meta.source_preview.trim().slice(0, 140);
  }
  const parts: string[] = [];
  if (typeof meta.skill === "string") parts.push(String(meta.skill).replace(/_/g, " "));
  if (typeof meta.channel === "string") parts.push(String(meta.channel).replace(/_/g, " "));
  if (typeof meta.provider === "string") {
    parts.push(String(meta.provider).replace(/_/g, " "));
  }
  if (typeof meta.mode === "string" && meta.mode !== "reflect" && meta.mode !== "rccs_hybrid") {
    parts.push(String(meta.mode).replace(/_/g, " "));
  }
  return parts.length ? parts.join(" · ") : undefined;
}

function sourcesFromEvent(event: ActivityEvent): number | undefined {
  const n = event.metadata?.sources_found ?? event.metadata?.num_results;
  return typeof n === "number" ? n : undefined;
}

/** Compact completed-run headline — one distinctive fact, not generic chrome. */
export function completedRunHeadline(run: AskRun): string {
  if (run.status === "failed" || run.status === "cancelled") {
    return "Search interrupted";
  }
  const blob = run.stages.map((s) => `${s.label} ${s.detail ?? ""}`).join(" ").toLowerCase();
  const campusLive =
    /campus|live web|approved website|official|agentic|perplexity|web search|rccs/.test(blob);
  const knowledge = /knowledge base|knowledge/.test(blob);
  const n = run.sourcesFound;
  const sourceBit =
    typeof n === "number" && n > 0
      ? `${n} source${n === 1 ? "" : "s"}`
      : null;

  if (campusLive && sourceBit) return `Campus live · ${sourceBit}`;
  if (campusLive) return "Campus live search";
  if (knowledge && sourceBit) return `Knowledge · ${sourceBit}`;
  if (knowledge) return "Knowledge search";
  if (sourceBit) return `Answer ready · ${sourceBit}`;
  return "Answer prepared";
}

export function visibleStages(run: AskRun, maxVisible = 4): {
  hiddenCount: number;
  stages: LiveStage[];
} {
  if (run.stages.length <= maxVisible) {
    return { hiddenCount: 0, stages: run.stages };
  }
  const hiddenCount = run.stages.length - maxVisible;
  return { hiddenCount, stages: run.stages.slice(-maxVisible) };
}

export function formatRunElapsed(run: AskRun, now = Date.now()): string | null {
  const end = run.completedAt ?? now;
  const ms = end - run.startedAt;
  if (ms < 100) return null;
  return `${(ms / 1000).toFixed(1)}s`;
}
