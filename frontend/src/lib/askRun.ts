/**
 * Trust-calibrated Ask run model.
 *
 * The backend can emit many low-level events, including parallel search branches.
 * This reducer preserves the full sanitized trace while the UI groups it into a
 * stable four-phase story: Understand → Search → Verify → Write.
 */

import type { ActivityEvent } from "../types";

export type AskRunStatus =
  | "queued"
  | "running"
  | "streaming"
  | "completed"
  | "failed"
  | "cancelled";

export type LiveStageStatus = "active" | "completed" | "failed" | "cancelled";
export type LivePhase = "understand" | "search" | "verify" | "compose";
export type LiveStageKind = "milestone" | "operation" | "evidence";
export type LivePhaseStatus = "pending" | "active" | "completed" | "failed" | "cancelled";

export interface LiveStage {
  id: string;
  event: string;
  label: string;
  detail?: string;
  status: LiveStageStatus;
  elapsedMs?: number;
  sequence: number;
  phase?: LivePhase;
  kind?: LiveStageKind;
  operationId?: string;
  sourceTitle?: string;
  sourceHost?: string;
  sourceUrl?: string;
  sourceType?: string;
  count?: number;
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
  sourcesRead?: number;
  citationsUsed?: number;
}

export interface LivePhaseView {
  id: LivePhase;
  label: string;
  status: LivePhaseStatus;
  headline: string;
  detail?: string;
  stages: LiveStage[];
}

export interface LiveTrailView {
  phases: LivePhaseView[];
  currentPhase: LivePhaseView;
  currentStage?: LiveStage;
  evidence: LiveStage[];
  trace: LiveStage[];
}

const PHASE_ORDER: LivePhase[] = ["understand", "search", "verify", "compose"];

const PHASE_LABELS: Record<LivePhase, string> = {
  understand: "Understand",
  search: "Search",
  verify: "Verify",
  compose: "Write",
};

const PHASE_FALLBACKS: Record<LivePhase, string> = {
  understand: "Understanding your question",
  search: "Searching trusted sources",
  verify: "Checking the evidence",
  compose: "Writing your answer",
};

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

function metadataOf(event: ActivityEvent): Record<string, unknown> {
  return (event.metadata ?? {}) as Record<string, unknown>;
}

function textMeta(meta: Record<string, unknown>, key: string): string | undefined {
  const value = meta[key];
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function numberMeta(meta: Record<string, unknown>, ...keys: string[]): number | undefined {
  for (const key of keys) {
    const value = meta[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
  }
  return undefined;
}

function validPhase(value: unknown): LivePhase | undefined {
  return value === "understand" || value === "search" || value === "verify" || value === "compose"
    ? value
    : undefined;
}

export function phaseForEvent(eventName: string, metadata?: Record<string, unknown>): LivePhase {
  const explicit = validPhase(metadata?.phase);
  if (explicit) return explicit;

  const name = eventName.toLowerCase();
  if (
    name.startsWith("request.") ||
    name.startsWith("query.") ||
    name.startsWith("plan.") ||
    name.startsWith("intent.")
  ) {
    return "understand";
  }
  if (
    name.startsWith("retrieval.") ||
    name.startsWith("search.") ||
    name.startsWith("source.") ||
    name.startsWith("page.") ||
    name.startsWith("tool.") ||
    name.startsWith("skill.")
  ) {
    return "search";
  }
  if (
    name.startsWith("reranking.") ||
    name.startsWith("evidence.") ||
    name.startsWith("citation.") ||
    name.startsWith("citations.") ||
    name.startsWith("validation.")
  ) {
    return "verify";
  }
  return "compose";
}

function kindForEvent(eventName: string, metadata: Record<string, unknown>): LiveStageKind {
  const explicit = metadata.kind;
  if (explicit === "milestone" || explicit === "operation" || explicit === "evidence") {
    return explicit;
  }

  const name = eventName.toLowerCase();
  if (
    name.includes("source_found") ||
    name.includes("source.found") ||
    name.includes("page.open") ||
    name.includes("page.read") ||
    metadata.source_title
  ) {
    return "evidence";
  }
  if (metadata.operation_id || metadata.skill || metadata.channel) return "operation";
  return "milestone";
}

function stageStatusForEvent(eventName: string): LiveStageStatus {
  const name = eventName.toLowerCase();
  if (name.includes("failed") || name.endsWith(".error")) return "failed";
  if (name.includes("cancelled") || name.includes("canceled")) return "cancelled";
  if (name.endsWith(".completed") || name.endsWith(".complete") || name.endsWith(".result")) {
    return "completed";
  }
  return "active";
}

function normalizedOperationId(
  eventName: string,
  phase: LivePhase,
  metadata: Record<string, unknown>,
): string {
  return (
    textMeta(metadata, "operation_id") ??
    textMeta(metadata, "skill") ??
    textMeta(metadata, "channel") ??
    `${phase}:${eventFamily(eventName)}`
  );
}

function eventFamily(eventName: string): string {
  return eventName
    .toLowerCase()
    .replace(/\.(started|completed|complete|result|progress|failed|error)$/, "")
    .replace(/_(started|completed|complete|result|progress|failed|error)$/, "");
}

function safeFallbackLabel(event: ActivityEvent): string {
  const message = typeof event.message === "string" ? event.message.replace(/\s+/g, " ").trim() : "";
  return message || "Working on your answer";
}

function narrateEvent(event: ActivityEvent, phase: LivePhase, metadata: Record<string, unknown>): string {
  const name = event.event.toLowerCase();
  const skill = textMeta(metadata, "skill");
  const n = numberMeta(metadata, "sources_found", "num_results", "result_count");
  const scope = textMeta(metadata, "source_scope") || textMeta(metadata, "mode");
  const backendMessage = typeof event.message === "string" ? event.message.trim() : "";
  const isResult =
    name.endsWith(".result") ||
    name.endsWith(".completed") ||
    name.endsWith(".complete") ||
    textMeta(metadata, "status") === "completed";

  // Prefer path-specific backend copy whenever it is present and safe.
  if (
    backendMessage &&
    (name === "query.classified" ||
      name === "intent.classified" ||
      name === "query.rewritten" ||
      name === "plan.created" ||
      skill === "query_planner" ||
      skill === "page_open" ||
      (isResult && Boolean(skill)) ||
      metadata.followup === true ||
      /citing:|using |including |follow-up|planner|opened|read/i.test(backendMessage))
  ) {
    return backendMessage;
  }

  if (name === "request.accepted") return "Starting your request";
  if (name === "query.analyzing") return "Understanding what you need";
  if (name === "query.rewritten") return backendMessage || "Refining the search terms";
  if (name === "query.classified" || name === "intent.classified") {
    return backendMessage || "Choosing the right search path";
  }
  if (name === "plan.created") return backendMessage || "Planning the search";

  // Skill start labels only — result events keep backend skill_result_message.
  if (!isResult) {
    if (skill === "kb_retrieve") return "Searching the McNeese knowledge base";
    if (skill === "official_web") return "Searching official McNeese websites";
    if (skill === "companion") return "Checking approved companion sources";
    if (skill === "agentic_web") return "Searching the live web";
    if (skill === "page_open") return "Reading selected pages";
    if (skill === "query_planner") return "Planning category searches";
    if (skill === "structured_specialist") return "Checking the specialized campus catalog path";
  } else if (backendMessage) {
    return backendMessage;
  }

  if (name === "retrieval.started" || name === "search.started") {
    if (backendMessage) return backendMessage;
    if (scope === "knowledge" || scope === "knowledge_base") return "Searching McNeese sources only";
    if (scope === "web" || scope === "web_search") {
      return "Searching official McNeese sources and the live web";
    }
    if (scope === "adaptive") return "Adaptive mode: choosing the best research path";
    return "Searching trusted McNeese sources";
  }
  if (name.includes("source_found") || name.includes("source.found")) {
    if (textMeta(metadata, "source_status") === "cited" || /^citing:/i.test(backendMessage)) {
      return backendMessage || "Selecting sources to cite";
    }
    return backendMessage || "Reading a relevant source";
  }
  if (name === "retrieval.completed" || name === "search.completed") {
    return typeof n === "number"
      ? `Collected ${n} relevant source${n === 1 ? "" : "s"}`
      : "Collected the relevant sources";
  }
  if (name === "reranking.started" || name === "evidence.ranking") {
    return "Ranking evidence by relevance";
  }
  if (name === "reranking.completed" || name === "evidence.selected") {
    return "Selected the strongest evidence";
  }
  if (name === "citations.validating" || name === "citation.validating") {
    return "Checking every citation";
  }
  if (name === "answer.outlining") return "Organizing the answer";
  if (name === "answer.generating") return "Writing your answer";
  if (name === "answer.completed") return "Answer ready";
  if (name === "request.failed" || name === "answer.failed") return "The request could not finish";

  return safeFallbackLabel(event) || PHASE_FALLBACKS[phase];
}

function detailForEvent(_event: ActivityEvent, metadata: Record<string, unknown>): string | undefined {
  const sourceTitle = textMeta(metadata, "source_title");
  const sourceHost = textMeta(metadata, "source_host");
  if (sourceTitle && sourceHost) return `${sourceTitle} · ${sourceHost}`;
  if (sourceTitle) return sourceTitle;

  // Compatibility with the current backend. New emitters should send one source_title per event.
  const preview = textMeta(metadata, "source_preview");
  if (preview) return preview.slice(0, 150);

  const operationLabel = textMeta(metadata, "operation_label");
  if (operationLabel) return operationLabel;

  const count = numberMeta(
    metadata,
    "sources_read",
    "sources_found",
    "num_results",
    "result_count",
    "selected_count",
    "citation_count",
  );
  if (typeof count === "number") return `${count} item${count === 1 ? "" : "s"}`;

  const mode = textMeta(metadata, "mode");
  if (mode && !["reflect", "rccs_hybrid", "supervisor_rccs"].includes(mode)) {
    return mode.replace(/_/g, " ");
  }
  return undefined;
}

function semanticEventKey(event: ActivityEvent): string {
  const meta = metadataOf(event);
  const eventId = textMeta(meta, "event_id");
  if (eventId) return `${event.requestId}|${event.runId ?? ""}|${eventId}`;

  return [
    event.requestId,
    event.runId ?? "",
    event.event,
    textMeta(meta, "operation_id") ?? textMeta(meta, "skill") ?? "",
    textMeta(meta, "source_title") ?? textMeta(meta, "source_preview") ?? "",
    numberMeta(meta, "sources_found", "num_results", "result_count") ?? "",
    typeof event.message === "string" ? event.message.trim() : "",
  ].join("|");
}

function sourceCountFromEvent(event: ActivityEvent): number | undefined {
  return numberMeta(metadataOf(event), "sources_found", "num_results", "result_count");
}

function sourcesReadFromEvent(event: ActivityEvent): number | undefined {
  return numberMeta(metadataOf(event), "sources_read");
}

function citationsFromEvent(event: ActivityEvent): number | undefined {
  return numberMeta(metadataOf(event), "citation_count", "citations_used");
}

function maxDefined(current: number | undefined, next: number | undefined): number | undefined {
  if (typeof next !== "number") return current;
  if (typeof current !== "number") return next;
  return Math.max(current, next);
}

function phaseIndex(phase: LivePhase): number {
  return PHASE_ORDER.indexOf(phase);
}

function shouldMergeStage(previous: LiveStage, next: LiveStage): boolean {
  if (previous.kind === "evidence" || next.kind === "evidence") {
    return Boolean(
      previous.sourceTitle &&
        next.sourceTitle &&
        previous.sourceTitle === next.sourceTitle &&
        previous.sourceHost === next.sourceHost,
    );
  }
  return previous.phase === next.phase && previous.operationId === next.operationId;
}

/** Map one sanitized backend event onto the run without pretending parallel work is linear. */
export function applyActivityEvent(run: AskRun, event: ActivityEvent): AskRun {
  if (event.requestId && run.requestId && event.requestId !== run.requestId) {
    console.warn("Ignoring unmatched AskMcNeese request", event.requestId, "expected", run.requestId);
    return run;
  }
  if (event.runId && event.runId !== run.runId) {
    console.warn("Ignoring unmatched AskMcNeese run", event.runId, "expected", run.runId);
    return run;
  }

  const key = semanticEventKey(event);
  if (run.processedEventKeys.includes(key)) return run;

  const metadata = metadataOf(event);
  const incomingStatus = stageStatusForEvent(event.event);
  const mappedPhase = phaseForEvent(event.event, metadata);
  const latestActivePhase = [...run.stages]
    .reverse()
    .find((stage) => stage.status === "active")?.phase;
  // A generic failure belongs to the phase that was actually running, not
  // automatically to "Write". Explicit backend phase metadata still wins.
  const phase =
    (incomingStatus === "failed" || incomingStatus === "cancelled") &&
    !validPhase(metadata.phase) &&
    latestActivePhase
      ? latestActivePhase
      : mappedPhase;
  const kind = kindForEvent(event.event, metadata);
  const operationId = normalizedOperationId(event.event, phase, metadata);
  const sourceTitle = textMeta(metadata, "source_title");
  const sourceHost = textMeta(metadata, "source_host");
  const sourceUrl = textMeta(metadata, "source_url");
  const sourceType = textMeta(metadata, "source_type");

  const incoming: LiveStage = {
    id: `stg-${run.runId}-${run.stages.length}`,
    event: event.event,
    label: narrateEvent(event, phase, metadata),
    detail: detailForEvent(event, metadata),
    status: incomingStatus,
    elapsedMs: event.elapsedMs,
    sequence: run.stages.length,
    phase,
    kind,
    operationId,
    sourceTitle,
    sourceHost,
    sourceUrl,
    sourceType,
    count: sourceCountFromEvent(event),
  };

  const existingIndex = [...run.stages]
    .map((stage, index) => ({ stage, index }))
    .reverse()
    .find(({ stage }) => shouldMergeStage(stage, incoming))?.index;

  let stages = run.stages.map((stage) => {
    if (stage.status !== "active") return stage;
    const stagePhase = stage.phase ?? phaseForEvent(stage.event);
    const movedToLaterPhase = phaseIndex(stagePhase) < phaseIndex(phase);
    const sameOperation = stage.operationId === operationId && stagePhase === phase;
    const incomingIsScoped = Boolean(
      metadata.operation_id || metadata.skill || metadata.channel || metadata.provider,
    );
    const stageIsScoped = Boolean(
      stage.operationId && !stage.operationId.startsWith(`${stagePhase}:`),
    );
    const sameUnscopedMilestone =
      stage.kind !== "evidence" &&
      kind !== "evidence" &&
      stagePhase === phase &&
      !incomingIsScoped &&
      !stageIsScoped;

    if (movedToLaterPhase || sameOperation || sameUnscopedMilestone) {
      return { ...stage, status: "completed" as const };
    }
    return stage;
  });

  if (typeof existingIndex === "number") {
    stages = stages.map((stage, index) =>
      index === existingIndex
        ? {
            ...stage,
            event: incoming.event,
            label: incoming.label,
            detail: incoming.detail ?? stage.detail,
            status: incoming.status,
            elapsedMs: incoming.elapsedMs ?? stage.elapsedMs,
            sourceTitle: incoming.sourceTitle ?? stage.sourceTitle,
            sourceHost: incoming.sourceHost ?? stage.sourceHost,
            sourceUrl: incoming.sourceUrl ?? stage.sourceUrl,
            sourceType: incoming.sourceType ?? stage.sourceType,
            count: incoming.count ?? stage.count,
          }
        : stage,
    );
  } else {
    stages = [...stages, incoming];
  }

  const eventName = event.event.toLowerCase();
  let status: AskRunStatus = run.status === "queued" ? "running" : run.status;
  if (phase === "compose" && incomingStatus === "active") status = "streaming";
  if (eventName === "answer.completed" || eventName === "request.completed") status = "completed";
  if (incomingStatus === "failed") status = "failed";
  if (incomingStatus === "cancelled") status = "cancelled";

  const terminal = status === "completed" || status === "failed" || status === "cancelled";

  return {
    ...run,
    status,
    stages,
    processedEventKeys: [...run.processedEventKeys, key],
    sourcesFound: maxDefined(run.sourcesFound, sourceCountFromEvent(event)),
    sourcesRead: maxDefined(run.sourcesRead, sourcesReadFromEvent(event)),
    citationsUsed: maxDefined(run.citationsUsed, citationsFromEvent(event)),
    completedAt: terminal ? Date.now() : run.completedAt,
  };
}

export function completeAskRun(run: AskRun, status: AskRunStatus = "completed"): AskRun {
  const finalStageStatus: LiveStageStatus =
    status === "cancelled" ? "cancelled" : status === "failed" ? "failed" : "completed";

  return {
    ...run,
    status,
    completedAt: Date.now(),
    stages: run.stages.map((stage) =>
      stage.status === "active" ? { ...stage, status: finalStageStatus } : stage,
    ),
  };
}

export function shouldShowLiveActivity(run: AskRun): boolean {
  return (
    run.status === "queued" ||
    run.status === "running" ||
    run.status === "streaming" ||
    run.status === "failed" ||
    run.status === "cancelled" ||
    run.stages.length > 0
  );
}

function phaseStatus(stages: LiveStage[], _runStatus: AskRunStatus): LivePhaseStatus {
  if (stages.some((stage) => stage.status === "failed")) return "failed";
  if (stages.some((stage) => stage.status === "cancelled")) return "cancelled";
  if (stages.some((stage) => stage.status === "active")) return "active";
  if (stages.length > 0) return "completed";
  return "pending";
}

function uniqueEvidence(stages: LiveStage[]): LiveStage[] {
  const seen = new Set<string>();
  const output: LiveStage[] = [];
  for (const stage of [...stages].reverse()) {
    const key = `${stage.sourceTitle ?? stage.detail ?? stage.label}|${stage.sourceHost ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    output.push(stage);
    if (output.length === 4) break;
  }
  return output.reverse();
}

export function buildLiveTrail(run: AskRun): LiveTrailView {
  const phases = PHASE_ORDER.map((phase): LivePhaseView => {
    const stages = run.stages.filter(
      (stage) => (stage.phase ?? phaseForEvent(stage.event)) === phase,
    );
    const latest = stages[stages.length - 1];
    return {
      id: phase,
      label: PHASE_LABELS[phase],
      status: phaseStatus(stages, run.status),
      headline: latest?.label ?? PHASE_FALLBACKS[phase],
      detail: latest?.detail,
      stages,
    };
  });

  const activePhase =
    [...phases].reverse().find((phase) => phase.status === "active") ??
    [...phases].reverse().find((phase) => phase.status !== "pending") ??
    phases[0];

  const currentStage =
    [...run.stages].reverse().find((stage) => stage.status === "active") ??
    run.stages[run.stages.length - 1];

  return {
    phases,
    currentPhase: activePhase,
    currentStage,
    evidence: uniqueEvidence(run.stages.filter((stage) => stage.kind === "evidence")),
    trace: run.stages,
  };
}

export function completedRunHeadline(run: AskRun): string {
  if (run.status === "failed") return "Search could not finish";
  if (run.status === "cancelled") return "Research stopped";

  const parts: string[] = [];
  if (typeof run.sourcesRead === "number" && run.sourcesRead > 0) {
    parts.push(`${run.sourcesRead} read`);
  } else if (typeof run.sourcesFound === "number" && run.sourcesFound > 0) {
    parts.push(`${run.sourcesFound} found`);
  }
  if (typeof run.citationsUsed === "number" && run.citationsUsed > 0) {
    parts.push(`${run.citationsUsed} cited`);
  }
  return parts.length ? `Research complete · ${parts.join(" · ")}` : "Research complete";
}

export function formatRunElapsed(run: AskRun, now = Date.now()): string | null {
  const end = run.completedAt ?? now;
  const ms = end - run.startedAt;
  if (ms < 100) return null;
  return `${(ms / 1000).toFixed(1)}s`;
}
