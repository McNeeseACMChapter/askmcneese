/**
 * Presentation mapper for the live research trail.
 * Converts AskRun stages into quiet narration — not a phase dashboard.
 */

import type { AskRun, LivePhase, LiveStage } from "./askRun";
import { completedRunHeadline, formatRunElapsed, phaseForEvent } from "./askRun";

export type NarrationCategory = LivePhase;

export interface ResearchEvidence {
  id: string;
  title: string;
  host?: string;
  url?: string;
}

export interface ResearchHistoryRow {
  id: string;
  label: string;
  status: "completed" | "failed" | "cancelled";
}

export interface ResearchNarration {
  currentLabel: string;
  currentDetail?: string;
  category: NarrationCategory;
  evidence: ResearchEvidence[];
  history: ResearchHistoryRow[];
  earlierCount: number;
  compact: boolean;
  result: "active" | "completed" | "failed" | "cancelled";
  completedTitle: string;
  elapsed: string | null;
  /** Screen-reader announcement key — category + label only (not every source). */
  announceKey: string;
  announceText: string;
}

const UNDERSTAND_EVENTS = new Set([
  "request.accepted",
  "query.analyzing",
  "query.rewritten",
  "query.classified",
  "plan.created",
]);

function categoryOf(stage: LiveStage): NarrationCategory {
  return stage.phase ?? phaseForEvent(stage.event);
}

function isEvidence(stage: LiveStage): boolean {
  return stage.kind === "evidence" || Boolean(stage.sourceTitle);
}

function normalizeSourceKey(stage: LiveStage): string {
  const url = (stage.sourceUrl ?? "").trim().toLowerCase();
  if (url) return `url:${url}`;
  const title = (stage.sourceTitle ?? stage.detail ?? stage.label).trim().toLowerCase();
  const host = (stage.sourceHost ?? "").trim().toLowerCase();
  return `title:${title}|${host}`;
}

function meaningfulHistoryLabel(stage: LiveStage): string | null {
  if (isEvidence(stage)) return null;
  const name = stage.event.toLowerCase();
  if (name.includes("source_found") || name.includes("page.open")) return null;

  // Keep path-specific backend/skill labels instead of collapsing everything.
  const label = (stage.label || "").trim();
  const distinctive =
    /follow-up|mcneese sources only|live web|official sources first|knowledge base|catalog|planner|agentic|companion|opened|read|citing|housing|career|degree|course/i.test(
      label,
    );

  if (UNDERSTAND_EVENTS.has(name) || categoryOf(stage) === "understand") {
    if (name === "request.accepted") return "Started your request";
    if (distinctive) return label;
    if (name === "query.classified" || name === "intent.classified") {
      return label || "Chose the search path";
    }
    return label || "Understood your question";
  }
  if (categoryOf(stage) === "search") {
    if (distinctive) return label;
    if (name.endsWith(".completed") || name.endsWith(".complete") || name.endsWith(".result")) {
      return stage.count
        ? `${label || "Searched sources"} · ${stage.count} found`
        : label || "Searched sources";
    }
    return label || "Searching sources";
  }
  if (categoryOf(stage) === "verify") {
    return distinctive ? label : label || "Checked sources and citations";
  }
  if (categoryOf(stage) === "compose") {
    if (name.includes("completed")) return "Finished writing";
    return null;
  }
  return label || null;
}

function currentLabelFor(stage: LiveStage | undefined, run: AskRun): string {
  if (!stage) {
    if (run.status === "queued" || run.stages.length === 0) return "Starting your request";
    return "Working on your answer";
  }
  const name = stage.event.toLowerCase();
  if (isEvidence(stage) || name.includes("source_found")) {
    if (/^citing:/i.test(stage.label) || stage.sourceType === "cited") {
      return stage.label;
    }
    return stage.label || "Reading relevant McNeese sources";
  }
  if (run.status === "streaming" || name === "answer.generating") {
    return "Writing your answer";
  }
  return stage.label;
}

function currentDetailFor(stage: LiveStage | undefined, evidence: ResearchEvidence[]): string | undefined {
  if (!stage) return undefined;
  if (isEvidence(stage) || stage.event.toLowerCase().includes("source_found")) {
    if (evidence.length === 0) return undefined;
    return evidence.length === 1
      ? "1 useful source found"
      : `${evidence.length} useful sources found`;
  }
  // Prefer operation detail over joined source_preview blobs
  if (stage.detail && !stage.detail.includes(" · ") && stage.detail.length < 80) {
    return stage.detail;
  }
  if (stage.count && categoryOf(stage) === "search") {
    return `${stage.count} useful source${stage.count === 1 ? "" : "s"} found`;
  }
  return undefined;
}

function collectEvidence(stages: LiveStage[]): ResearchEvidence[] {
  const seen = new Set<string>();
  const out: ResearchEvidence[] = [];
  for (const stage of [...stages].reverse()) {
    if (!isEvidence(stage) && !stage.sourceTitle) continue;
    const title = (stage.sourceTitle ?? stage.detail ?? "").trim();
    if (!title || title.includes(" · ")) continue;
    const key = normalizeSourceKey(stage);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      id: stage.id,
      title,
      host: stage.sourceHost,
      url: stage.sourceUrl,
    });
    if (out.length >= 4) break;
  }
  return out.reverse();
}

function collectHistory(stages: LiveStage[], currentId?: string): {
  history: ResearchHistoryRow[];
  earlierCount: number;
} {
  const rows: ResearchHistoryRow[] = [];
  const seenLabels = new Set<string>();

  for (const stage of stages) {
    if (stage.id === currentId) continue;
    if (stage.status === "active") continue;
    const label = meaningfulHistoryLabel(stage);
    if (!label) continue;
    const key = label.toLowerCase();
    if (seenLabels.has(key)) continue;
    seenLabels.add(key);
    rows.push({
      id: stage.id,
      label,
      status:
        stage.status === "failed"
          ? "failed"
          : stage.status === "cancelled"
            ? "cancelled"
            : "completed",
    });
  }

  const visible = rows.slice(-3);
  return {
    history: visible,
    earlierCount: Math.max(0, rows.length - visible.length),
  };
}

export function buildResearchNarration(run: AskRun): ResearchNarration {
  const evidenceAll = collectEvidence(run.stages);
  const active =
    run.status === "queued" || run.status === "running" || run.status === "streaming";
  const compact = run.status === "streaming";

  const currentStage =
    [...run.stages].reverse().find((s) => s.status === "active") ??
    run.stages[run.stages.length - 1];

  const category: NarrationCategory = currentStage
    ? categoryOf(currentStage)
    : "understand";

  const currentLabel = compact
    ? "Writing your answer"
    : currentLabelFor(currentStage, run);
  const currentDetail = compact
    ? undefined
    : currentDetailFor(currentStage, evidenceAll);

  const evidence = compact ? [] : evidenceAll.slice(-2);
  const { history, earlierCount } = collectHistory(run.stages, currentStage?.id);

  let result: ResearchNarration["result"] = "active";
  if (!active) {
    if (run.status === "failed") result = "failed";
    else if (run.status === "cancelled") result = "cancelled";
    else result = "completed";
  }

  const announceKey = `${category}|${currentLabel}`;
  const announceText = currentDetail
    ? `${currentLabel}. ${currentDetail}`
    : currentLabel;

  return {
    currentLabel,
    currentDetail,
    category,
    evidence,
    history: active ? history : [],
    earlierCount: active ? earlierCount : 0,
    compact,
    result,
    completedTitle: completedRunHeadline(run),
    elapsed: formatRunElapsed(run),
    announceKey,
    announceText,
  };
}

/** Timeout fallback copy — never marks phases complete. */
export function timeoutFallbackDetail(
  narration: ResearchNarration,
  quietMs: number,
  hasRealStages: boolean,
): string | undefined {
  if (narration.compact || narration.result !== "active") return undefined;
  // No SSE frames yet — usually means the API has not connected / responded.
  if (!hasRealStages) {
    if (quietMs >= 8000) return "Still waiting for AskMcNeese…";
    if (quietMs >= 2500) return "Connecting to the server";
    return undefined;
  }
  if (narration.category === "understand" && quietMs >= 2500) {
    return "Choosing the best McNeese sources";
  }
  if (narration.category === "search" && quietMs >= 4000) {
    return "Still searching approved sources";
  }
  return undefined;
}
