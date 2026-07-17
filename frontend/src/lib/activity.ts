import type { ActivityEvent, PipelineStep } from "../types";

/** Fallback copy aligned with backend/app/services/activity_events.py SAFE_MESSAGES. */
const SAFE_MESSAGES: Record<string, string> = {
  "request.accepted": "Got your question — starting now",
  "query.analyzing": "Reading your question to decide what to search",
  "query.rewritten": "Clarified the search terms for better results",
  "retrieval.started": "Searching McNeese-approved sources",
  "retrieval.source_found": "Found useful sources",
  "retrieval.completed": "Finished collecting sources",
  "reranking.started": "Checking whether we have enough good sources",
  "reranking.completed": "Sources look ready for an answer",
  "answer.generating": "Writing your answer from those sources",
  "citations.validating": "Double-checking the source links",
  "answer.completed": "Answer ready",
  "request.failed": "Something went wrong — please try again",
};

const ALLOWED_METADATA = new Set([
  "sources_found",
  "num_results",
  "mode",
  "duration_ms",
  "status",
  "channel",
  "provider",
  "skill",
  "source_preview",
]);

function looksSensitive(value: string): boolean {
  return /(?:[a-z]:\\|\/(?:users|home|var|etc)\/|api[_ -]?key|token|secret|\.env)/i.test(value);
}

export function sanitizeActivityMessage(message: unknown, event = ""): string {
  if (typeof message !== "string" || !message.trim() || looksSensitive(message)) {
    return SAFE_MESSAGES[event] ?? "Working on your answer";
  }
  return message.replace(/\s+/g, " ").trim().slice(0, 220);
}

function safeMetadata(value: unknown): ActivityEvent["metadata"] {
  if (!value || typeof value !== "object") return undefined;
  const output: NonNullable<ActivityEvent["metadata"]> = {};
  Object.entries(value).forEach(([key, item]) => {
    if (
      ALLOWED_METADATA.has(key) &&
      (typeof item === "number" ||
        typeof item === "boolean" ||
        item === null ||
        (typeof item === "string" && !looksSensitive(item)))
    ) {
      output[key] = item;
    }
  });
  return Object.keys(output).length ? output : undefined;
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
    metadata: safeMetadata(payload.metadata),
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
    metadata: { status: step.status },
  };
}

export { SAFE_MESSAGES };
