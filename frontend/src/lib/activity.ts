import type { ActivityEvent, PipelineStep } from "../types";

/**
 * Frontend boundary for live telemetry.
 * The server may describe real work, but only structured, allowlisted facts cross
 * into the UI. Raw terminal output, prompts, file paths, stack traces, and secrets do not.
 */

const SAFE_MESSAGES: Record<string, string> = {
  "request.accepted": "Starting your request",
  "query.analyzing": "Understanding what you need",
  "query.classified": "Choosing the right search path",
  "query.rewritten": "Refining the search terms",
  "plan.created": "Planning the search",
  "retrieval.started": "Searching trusted McNeese sources",
  "retrieval.source_found": "Reading a relevant source",
  "retrieval.completed": "Collected the relevant sources",
  "reranking.started": "Ranking evidence by relevance",
  "reranking.completed": "Selected the strongest evidence",
  "answer.outlining": "Organizing the answer",
  "answer.generating": "Writing your answer",
  "citations.validating": "Checking every citation",
  "answer.completed": "Answer ready",
  "request.failed": "The request could not finish",
};

const ALLOWED_METADATA = new Set([
  "schema_version",
  "event_id",
  "phase",
  "kind",
  "visibility",
  "operation_id",
  "operation_label",
  "sources_found",
  "sources_read",
  "num_results",
  "result_count",
  "selected_count",
  "citation_count",
  "citations_used",
  "mode",
  "duration_ms",
  "status",
  "channel",
  "provider",
  "skill",
  "source_type",
  "source_title",
  "source_host",
  "source_url",
  "source_status",
  "planned_query_count",
  "source_scope",
  "primary_intent",
  "category",
  // Temporary compatibility with the old backend. Prefer source_title + source_host.
  "source_preview",
]);

const MAX_MESSAGE_LENGTH = 180;
const MAX_METADATA_STRING = 160;

function looksSensitive(value: string): boolean {
  return /(?:bearer\s+[a-z0-9._-]+|api[_ -]?key|access[_ -]?token|secret|password|\.env|stack trace|traceback|[a-z]:\\|\/(?:users|home|var|etc|private|tmp)\/)/i.test(
    value,
  );
}

function cleanString(value: string, max = MAX_METADATA_STRING): string | undefined {
  const cleaned = value.replace(/\s+/g, " ").trim();
  if (!cleaned || looksSensitive(cleaned)) return undefined;
  return cleaned.slice(0, max);
}

function cleanPublicUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" && url.protocol !== "http:") return undefined;
    if (url.username || url.password) return undefined;
    const host = url.hostname.toLowerCase();
    if (
      host === "localhost" ||
      host === "127.0.0.1" ||
      host === "::1" ||
      host.endsWith(".local")
    ) return undefined;
    return url.toString().slice(0, 500);
  } catch {
    return undefined;
  }
}

export function sanitizeActivityMessage(message: unknown, event = ""): string {
  if (typeof message !== "string") return SAFE_MESSAGES[event] ?? "Working on your answer";
  return cleanString(message, MAX_MESSAGE_LENGTH) ?? SAFE_MESSAGES[event] ?? "Working on your answer";
}

function safeMetadata(value: unknown): ActivityEvent["metadata"] {
  if (!value || typeof value !== "object") return undefined;
  const output: Record<string, string | number | boolean | null> = {};

  Object.entries(value as Record<string, unknown>).forEach(([key, item]) => {
    if (!ALLOWED_METADATA.has(key)) return;
    if (typeof item === "string") {
      const cleaned = key === "source_url" ? cleanPublicUrl(item) : cleanString(item);
      if (cleaned) output[key] = cleaned;
      return;
    }
    if (typeof item === "number" && Number.isFinite(item)) {
      output[key] = item;
      return;
    }
    if (typeof item === "boolean") {
      output[key] = item;
      return;
    }
    if (item === null) output[key] = null;
  });

  return Object.keys(output).length ? (output as ActivityEvent["metadata"]) : undefined;
}

function mergedMetadata(payload: Record<string, unknown>): ActivityEvent["metadata"] {
  const raw: Record<string, unknown> = {
    ...(payload.metadata && typeof payload.metadata === "object"
      ? (payload.metadata as Record<string, unknown>)
      : {}),
  };

  // Schema v2 may place these fields at the top level. Normalize them into metadata
  // so the existing ActivityEvent shape remains backward compatible.
  ALLOWED_METADATA.forEach((key) => {
    if (payload[key] !== undefined && raw[key] === undefined) raw[key] = payload[key];
  });
  return safeMetadata(raw);
}

export function mapActivityPayload(payload: Record<string, unknown>): ActivityEvent {
  const event = typeof payload.event === "string" ? payload.event : "activity";
  return {
    requestId:
      typeof payload.request_id === "string"
        ? payload.request_id
        : typeof payload.requestId === "string"
          ? payload.requestId
          : "",
    runId:
      typeof payload.run_id === "string"
        ? payload.run_id
        : typeof payload.runId === "string"
          ? payload.runId
          : undefined,
    event,
    message: sanitizeActivityMessage(payload.message, event),
    elapsedMs:
      typeof payload.elapsed_ms === "number"
        ? payload.elapsed_ms
        : typeof payload.elapsedMs === "number"
          ? payload.elapsedMs
          : undefined,
    metadata: mergedMetadata(payload),
  };
}

export function mapLegacyStep(payload: Record<string, unknown>, requestId = ""): ActivityEvent {
  const step = payload as unknown as PipelineStep;
  const suffix =
    step.status === "completed" ? "completed" : step.status === "failed" ? "failed" : "started";
  const name = step.step === "generation" ? "answer" : step.step || "request";
  return {
    requestId,
    event: `${name}.${suffix}`,
    message: sanitizeActivityMessage(step.message, `${name}.${suffix}`),
    elapsedMs: typeof step.duration_ms === "number" ? step.duration_ms : undefined,
    metadata: { status: step.status } as ActivityEvent["metadata"],
  };
}
