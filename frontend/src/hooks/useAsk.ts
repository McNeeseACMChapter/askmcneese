import { useCallback, useRef, useState } from "react";
import { getApiBase } from "../lib/api";
import { getGuestToken } from "../features/onboarding/onboardingApi";
import { mapActivityPayload, sanitizeActivityMessage } from "../lib/activity";
import { normalizeAskResponse } from "../lib/answerModel";
import type { ActivityEvent, AskResponse, ChatMessage, Citation, SourceScope } from "../types";

export type AskStatus =
  | "idle"
  | "connecting"
  | "searching"
  | "generating"
  | "complete"
  | "stopped"
  | "error";

/** Request-scoped mesh / visual lifecycle — independent of session welcome state. */
export type AskRequestPhase = "idle" | "submitting" | "streaming";

export interface AskRequestVisualState {
  requestId: number;
  phase: AskRequestPhase;
}

export interface AskHistoryTurn {
  role: string;
  content: string;
}

export interface AskIdentity {
  requestId: string;
  turnId: string;
  assistantMessageId: string;
  runId: string;
  userMessageId?: string;
}

export type AskActivityListener = (event: ActivityEvent) => void;

interface UseAskReturn {
  ask: (
    question: string,
    sourceScope?: SourceScope,
    onStreamUpdate?: (text: string) => void,
    history?: AskHistoryTurn[],
    identity?: AskIdentity,
    onActivity?: AskActivityListener,
  ) => Promise<ChatMessage | null>;
  stop: () => void;
  isLoading: boolean;
  status: AskStatus;
  activity: ActivityEvent[];
  error: string | null;
  requestVisualState: AskRequestVisualState;
}

export function useAsk(): UseAskReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<AskStatus>("idle");
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [requestVisualState, setRequestVisualState] = useState<AskRequestVisualState>({
    requestId: 0,
    phase: "idle",
  });
  const abortRef = useRef<AbortController | null>(null);
  const loadingRef = useRef(false);
  const requestSequenceRef = useRef(0);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("stopped");
    const requestId = requestSequenceRef.current;
    setRequestVisualState({ requestId, phase: "idle" });
  }, []);

  const ask = useCallback(async (
    question: string,
    sourceScope: SourceScope = "adaptive",
    onStreamUpdate?: (text: string) => void,
    history?: AskHistoryTurn[],
    identity?: AskIdentity,
    onActivity?: AskActivityListener,
  ): Promise<ChatMessage | null> => {
    if (loadingRef.current) return null;

    const requestId = ++requestSequenceRef.current;
    // Prefer aborting any prior in-flight controller before claiming the new request.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    loadingRef.current = true;
    setIsLoading(true);
    setError(null);
    setStatus("connecting");
    setActivity([]);
    setRequestVisualState({
      requestId,
      phase: "submitting",
    });

    let streamStarted = false;
    const markStreaming = () => {
      if (requestSequenceRef.current !== requestId || streamStarted) return;
      streamStarted = true;
      setRequestVisualState({
        requestId,
        phase: "streaming",
      });
    };

    try {
      /*
       * Stream EOF + ChatMessage (answer, citations, metadata) are built inside
       * askWithStream before this returns. Only then does finally move phase to idle.
       */
      return await askWithStream(
        question,
        sourceScope,
        onStreamUpdate,
        controller.signal,
        setStatus,
        setActivity,
        history,
        identity,
        onActivity,
        markStreaming,
      );
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setStatus("stopped");
        setError(null);
        return null;
      }
      setStatus("error");
      const message = offlineFriendlyError(err);
      setError(message);
      const failedEvent: ActivityEvent = {
        requestId: identity?.requestId ?? "",
        runId: identity?.runId,
        event: "request.failed",
        message,
      };
      setActivity((previous) => appendUniqueActivity(previous, failedEvent));
      onActivity?.(failedEvent);
      return createErrorMessage(message, identity?.assistantMessageId);
    } finally {
      /*
       * An older request must never switch off the mesh belonging to a newer request.
       */
      if (requestSequenceRef.current === requestId) {
        setRequestVisualState({
          requestId,
          phase: "idle",
        });
      }
      loadingRef.current = false;
      abortRef.current = null;
      setIsLoading(false);
    }
  }, []);

  return { ask, stop, isLoading, status, activity, error, requestVisualState };
}

async function askWithStream(
  question: string,
  sourceScope: SourceScope,
  onStreamUpdate: ((text: string) => void) | undefined,
  signal: AbortSignal,
  setStatus: (s: AskStatus) => void,
  setActivity: (fn: (events: ActivityEvent[]) => ActivityEvent[]) => void,
  history?: AskHistoryTurn[],
  identity?: AskIdentity,
  onActivity?: AskActivityListener,
  onVisualStreamStart?: () => void,
): Promise<ChatMessage> {
  setStatus("searching");
  // Fail fast when the API never answers (dead worker / wrong port).
  // After headers arrive, the stream may run longer without this timer.
  const connectTimeoutMs = 12_000;
  const connectController = new AbortController();
  const connectTimer = window.setTimeout(() => {
    connectController.abort();
  }, connectTimeoutMs);
  const fetchSignal =
    typeof AbortSignal !== "undefined" && "any" in AbortSignal
      ? AbortSignal.any([signal, connectController.signal])
      : signal;

  const presenter = createPacedPresenter(onStreamUpdate, signal);
  const guestToken = getGuestToken();
  let res: Response;
  try {
    res = await fetch(`${getApiBase()}/ask`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        ...(guestToken ? { "X-Guest-Token": guestToken } : {}),
      },
      body: JSON.stringify({
        question,
        stream: true,
        source_scope: sourceScope,
        use_web_search: sourceScope === "web" || sourceScope === "adaptive",
        history: history ?? null,
        request_id: identity?.requestId,
        turn_id: identity?.turnId,
        run_id: identity?.runId,
        user_message_id: identity?.userMessageId,
        assistant_message_id: identity?.assistantMessageId,
      }),
      signal: fetchSignal,
    });
  } catch (err) {
    if (
      connectController.signal.aborted &&
      !(signal.aborted) &&
      err instanceof Error &&
      err.name === "AbortError"
    ) {
      throw new Error(
        "AskMcNeese did not respond in time. Check that the API is running, then try again.",
      );
    }
    throw err;
  } finally {
    window.clearTimeout(connectTimer);
  }

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error("This beta guest has used all 10 available questions.");
    }
    if (res.status === 401) {
      throw new Error("Your guest session expired. Refresh the page and try again.");
    }
    throw new Error(`Request failed (${res.status})`);
  }
  window.dispatchEvent(new Event("askmcneese:usage-changed"));

  const reader = res.body?.getReader();
  if (!reader) throw new Error("The response stream was unavailable");

  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";
  let citations: Citation[] = [];
  let queryId = identity?.requestId ?? "";
  let numResults = 0;
  let donePayload: Record<string, unknown> = {};
  let sawTerminalActivity = false;
  const emittedKeys = new Set<string>();

  const emitActivity = (event: ActivityEvent) => {
    const key = activityKey(event);
    if (emittedKeys.has(key)) return;
    emittedKeys.add(key);
    if (
      event.event === "answer.completed" ||
      event.event === "request.failed" ||
      event.event === "answer.failed" ||
      event.event === "request.cancelled"
    ) {
      sawTerminalActivity = true;
    }
    setActivity((previous) => appendUniqueActivity(previous, event));
    onActivity?.(event);
  };

  let sawDone = false;
  const ingestFrame = (frame: string) => {
    const parsed = parseFrame(frame);
    if (!parsed) return;
    const { event, data } = parsed;
    // First SSE frame marks visual "streaming"; do not clear the mesh here.
    onVisualStreamStart?.();
    if (event === "activity") {
      const mapped = mapActivityPayload(data);
      if (!mapped.requestId && identity?.requestId) mapped.requestId = identity.requestId;
      if (!mapped.runId && identity?.runId) mapped.runId = identity.runId;

      const requestMismatch =
        Boolean(identity?.requestId) &&
        Boolean(mapped.requestId) &&
        mapped.requestId !== identity?.requestId;
      const runMismatch =
        Boolean(identity?.runId) &&
        Boolean(mapped.runId) &&
        mapped.runId !== identity?.runId;
      if (requestMismatch || runMismatch) {
        console.warn("Ignoring unmatched AskMcNeese activity event", mapped);
        return;
      }

      emitActivity(mapped);
      if (mapped.event.startsWith("answer.") && mapped.event !== "answer.completed") {
        setStatus("generating");
      }
    } else if (event === "step" || data.step) {
      // Legacy step frames update broad status only. Canonical activity owns the trail.
      setStatus(data.step === "generation" ? "generating" : "searching");
    } else if (event === "chunk") {
      if (typeof data.text === "string") {
        fullText += data.text;
        presenter.push(fullText);
      }
      setStatus("generating");
    } else if (event === "citations" || Array.isArray(data.citations)) {
      citations = validCitations(data.citations);
      numResults = citations.length;
    } else if (event === "done") {
      sawDone = true;
      queryId = typeof data.query_id === "string" ? data.query_id : queryId;
      numResults = typeof data.num_results === "number" ? data.num_results : numResults;
      donePayload = data;
      // Prefer the backend's canonical body. Chunks can be partial/duplicated on fallback.
      const canonical =
        (typeof data.content_markdown === "string" && data.content_markdown.trim()
          ? data.content_markdown
          : null) ??
        (typeof data.answer === "string" && data.answer.trim() ? data.answer : null);
      if (canonical) {
        fullText = canonical;
        presenter.push(fullText);
      }
      setStatus("complete");

      // Some backends already emit answer.completed. Add a compatibility event only once.
      if (!sawTerminalActivity) {
        emitActivity({
          // Ownership must remain the request id; query_id is a result identifier, not a run id.
          requestId: identity?.requestId ?? "",
          runId: identity?.runId,
          event: "answer.completed",
          message: "Answer ready",
          elapsedMs: typeof data.total_ms === "number" ? data.total_ms : undefined,
          metadata: {
            ...(typeof data.num_results === "number" ? { num_results: data.num_results } : {}),
            citation_count: citations.length,
            phase: "compose",
            kind: "milestone",
          } as ActivityEvent["metadata"],
        });
      }
    } else if (event === "error") {
      throw new Error(sanitizeActivityMessage(data.message, "request.failed"));
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) ingestFrame(frame);
  }
  // Flush a final partial frame (EOF without trailing blank line).
  buffer += decoder.decode().replace(/\r\n/g, "\n");
  if (buffer.trim()) ingestFrame(buffer);

  if (!sawDone && !fullText.trim()) {
    throw new Error("The answer stream ended before a complete response arrived.");
  }

  if (!sawTerminalActivity) {
    emitActivity({
      requestId: identity?.requestId ?? "",
      runId: identity?.runId,
      event: "answer.completed",
      message: "Answer ready",
      metadata: {
        num_results: numResults,
        citation_count: citations.length,
        phase: "compose",
        kind: "milestone",
      } as ActivityEvent["metadata"],
    });
  }

  await presenter.finish(fullText);
  setStatus("complete");
  const contentMarkdown =
    typeof donePayload.content_markdown === "string" && donePayload.content_markdown.trim()
      ? donePayload.content_markdown
      : fullText;
  const response: AskResponse = {
    question,
    answer: fullText || contentMarkdown,
    chunks: [],
    num_results: numResults,
    query_id: queryId,
    sources: citations,
    answer_type: typeof donePayload.answer_type === "string"
      ? (donePayload.answer_type as AskResponse["answer_type"])
      : undefined,
    title: typeof donePayload.title === "string" ? donePayload.title : undefined,
    summary: typeof donePayload.summary === "string" ? donePayload.summary : undefined,
    content_markdown: contentMarkdown,
    key_facts: Array.isArray(donePayload.key_facts)
      ? (donePayload.key_facts as AskResponse["key_facts"])
      : undefined,
    important_dates: Array.isArray(donePayload.important_dates)
      ? (donePayload.important_dates as AskResponse["important_dates"])
      : undefined,
    requirements: Array.isArray(donePayload.requirements)
      ? (donePayload.requirements as string[])
      : undefined,
    steps: Array.isArray(donePayload.steps) ? (donePayload.steps as string[]) : undefined,
    warnings: Array.isArray(donePayload.warnings) ? (donePayload.warnings as string[]) : undefined,
    related_questions: Array.isArray(donePayload.related_questions)
      ? (donePayload.related_questions as string[])
      : undefined,
    confidence:
      donePayload.confidence === "high" ||
      donePayload.confidence === "medium" ||
      donePayload.confidence === "low"
        ? donePayload.confidence
        : undefined,
  };
  const structured = normalizeAskResponse(response);
  const assistantId =
    identity?.assistantMessageId ??
    `a-${Date.now()}-${(queryId || "local").slice(0, 8)}`;
  const displayText = (fullText || structured.contentMarkdown || "").trim();
  return {
    id: assistantId,
    role: "assistant",
    text: displayText,
    citations: citations.length > 0 ? citations : undefined,
    structured,
    confidence: structured.confidence,
    timestamp: new Date(),
    runId: identity?.runId,
  };
}

function activityKey(event: ActivityEvent): string {
  const metadata = (event.metadata ?? {}) as Record<string, unknown>;
  const eventId = typeof metadata.event_id === "string" ? metadata.event_id : "";
  if (eventId) return `${event.requestId}|${event.runId ?? ""}|${eventId}`;
  return [
    event.requestId,
    event.runId ?? "",
    event.event,
    typeof metadata.operation_id === "string" ? metadata.operation_id : "",
    typeof metadata.source_title === "string" ? metadata.source_title : "",
    event.message,
  ].join("|");
}

function appendUniqueActivity(events: ActivityEvent[], event: ActivityEvent): ActivityEvent[] {
  const key = activityKey(event);
  return events.some((existing) => activityKey(existing) === key) ? events : [...events, event];
}

function parseFrame(frame: string): { event: string; data: Record<string, unknown> } | null {
  let event = "message";
  const dataLines: string[] = [];
  frame.split("\n").forEach((line) => {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
  });
  if (!dataLines.length) return null;
  try {
    const data = JSON.parse(dataLines.join("\n")) as Record<string, unknown>;
    return { event, data };
  } catch {
    return null;
  }
}

function validCitations(value: unknown): Citation[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item, index) => {
    if (!item || typeof item !== "object") return [];
    const citation = item as Record<string, unknown>;
    const url = typeof citation.url === "string" ? citation.url.trim() : "";
    const title =
      typeof citation.title === "string" && citation.title.trim()
        ? citation.title.trim()
        : url;
    if (!url || !title) return [];
    const id =
      typeof citation.id === "string" && citation.id.trim()
        ? citation.id.trim()
        : `cite-${index}-${url}`;
    return [{
      id,
      title,
      url,
      snippet: typeof citation.snippet === "string" ? citation.snippet : undefined,
    }];
  });
}

function createErrorMessage(text: string, assistantMessageId?: string): ChatMessage {
  return {
    id: assistantMessageId ?? `e-${Date.now()}`,
    role: "assistant",
    text: text || "I couldn’t complete that request. Please try again.",
    isDemo: false,
    isError: true,
    isStreaming: false,
    timestamp: new Date(),
  };
}

function offlineFriendlyError(error: unknown): string {
  const text = error instanceof Error ? error.message : "";
  if (/did not respond in time/i.test(text)) {
    return text;
  }
  if (/fetch|network|connect|load failed/i.test(text)) {
    return "AskMcNeese is currently unreachable. Check your connection and try again.";
  }
  if (/used all 10 available questions/i.test(text)) {
    return "You’ve used all 10 questions available to this beta guest.";
  }
  if (/guest session expired/i.test(text)) {
    return "Your guest session expired. Refresh the page and try again.";
  }
  if (/request failed \(\d+\)/i.test(text)) {
    return "I couldn’t complete that request. Please try again.";
  }
  return "I couldn’t complete that request. Please try again.";
}
interface PacedPresenter {
  push: (text: string) => void;
  finish: (text: string) => Promise<void>;
}

function createPacedPresenter(
  onUpdate: ((text: string) => void) | undefined,
  signal: AbortSignal,
): PacedPresenter {
  if (!onUpdate) return { push: () => undefined, finish: async () => undefined };

  let target = "";
  let visible = "";
  let timer: number | null = null;
  let finishing = false;
  let resolveFinish: (() => void) | null = null;

  const stopTimer = () => {
    if (timer != null) window.clearInterval(timer);
    timer = null;
  };

  const tick = () => {
    if (signal.aborted) {
      stopTimer();
      resolveFinish?.();
      resolveFinish = null;
      return;
    }
    const remaining = target.length - visible.length;
    if (remaining <= 0) {
      stopTimer();
      if (finishing) {
        resolveFinish?.();
        resolveFinish = null;
      }
      return;
    }

    const step = finishing
      ? Math.max(24, Math.ceil(remaining / 8))
      : Math.max(8, Math.min(72, Math.ceil(remaining * 0.12)));
    let end = Math.min(target.length, visible.length + step);
    if (end < target.length) {
      const boundary = target.indexOf(" ", end);
      if (boundary > end && boundary - end < 20) end = boundary + 1;
    }
    visible = target.slice(0, end);
    onUpdate(visible);
  };

  const ensureTimer = () => {
    if (timer == null) timer = window.setInterval(tick, 32);
  };

  return {
    push(text) {
      if (text.length < target.length) visible = "";
      target = text;
      ensureTimer();
      tick();
    },
    finish(text) {
      target = text;
      finishing = true;
      if (visible === target) {
        stopTimer();
        return Promise.resolve();
      }
      ensureTimer();
      return new Promise<void>((resolve) => {
        resolveFinish = resolve;
        tick();
      });
    },
  };
}
