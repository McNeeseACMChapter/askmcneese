import { useCallback, useRef, useState } from "react";
import { getApiBase } from "../lib/api";
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

interface UseAskReturn {
  ask: (
    question: string,
    sourceScope?: SourceScope,
    onStreamUpdate?: (text: string) => void,
    history?: AskHistoryTurn[],
    identity?: AskIdentity,
  ) => Promise<ChatMessage | null>;
  stop: () => void;
  isLoading: boolean;
  status: AskStatus;
  activity: ActivityEvent[];
  error: string | null;
}

export function useAsk(): UseAskReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<AskStatus>("idle");
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const loadingRef = useRef(false);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("stopped");
  }, []);

  const ask = useCallback(async (
    question: string,
    sourceScope: SourceScope = "adaptive",
    onStreamUpdate?: (text: string) => void,
    history?: AskHistoryTurn[],
    identity?: AskIdentity,
  ): Promise<ChatMessage | null> => {
    if (loadingRef.current) return null;
    const controller = new AbortController();
    abortRef.current = controller;
    loadingRef.current = true;
    setIsLoading(true);
    setError(null);
    setStatus("connecting");
    setActivity([]);

    try {
      return await askWithStream(
        question,
        sourceScope,
        onStreamUpdate,
        controller.signal,
        setStatus,
        setActivity,
        history,
        identity,
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
      setActivity((previous) => [
        ...previous,
        {
          requestId: identity?.requestId ?? "",
          event: "request.failed",
          message,
        },
      ]);
      return createErrorMessage(message, identity?.assistantMessageId);
    } finally {
      loadingRef.current = false;
      abortRef.current = null;
      setIsLoading(false);
    }
  }, []);

  return { ask, stop, isLoading, status, activity, error };
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
): Promise<ChatMessage> {
  setStatus("searching");
  const res = await fetch(`${getApiBase()}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      question,
      stream: true,
      use_web_search: sourceScope === "web" || sourceScope === "adaptive",
      history: history ?? null,
      request_id: identity?.requestId,
      turn_id: identity?.turnId,
      run_id: identity?.runId,
      user_message_id: identity?.userMessageId,
      assistant_message_id: identity?.assistantMessageId,
    }),
    signal,
  });

  if (!res.ok) throw new Error(`Request failed (${res.status})`);

  const reader = res.body?.getReader();
  if (!reader) throw new Error("The response stream was unavailable");

  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";
  let citations: Citation[] = [];
  let queryId = identity?.requestId ?? "";
  let numResults = 0;
  let donePayload: Record<string, unknown> = {};

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const parsed = parseFrame(frame);
      if (!parsed) continue;
      const { event, data } = parsed;
      if (event === "activity") {
        const mapped = mapActivityPayload(data);
        if (!mapped.requestId && identity?.requestId) {
          mapped.requestId = identity.requestId;
        }
        if (!mapped.runId && identity?.runId) {
          mapped.runId = identity.runId;
        }
        // Ignore events that cannot be associated with this ask identity.
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
          continue;
        }
        setActivity((previous) => [...previous, mapped]);
        if (mapped.event.startsWith("answer.")) setStatus("generating");
      } else if (event === "step" || data.step) {
        // Status only — canonical `activity` owns the live trail (avoids near-duplicate rows).
        setStatus(data.step === "generation" ? "generating" : "searching");
      } else if (event === "chunk") {
        if (typeof data.text === "string") {
          fullText += data.text;
          onStreamUpdate?.(fullText);
        }
        setStatus("generating");
      } else if (event === "citations" || Array.isArray(data.citations)) {
        citations = validCitations(data.citations);
        numResults = citations.length;
      } else if (event === "done") {
        queryId = typeof data.query_id === "string" ? data.query_id : queryId;
        numResults = typeof data.num_results === "number" ? data.num_results : numResults;
        if (typeof data.answer === "string" && data.answer && !fullText) {
          fullText = data.answer;
        }
        donePayload = data;
        setStatus("complete");
        setActivity((previous) => [
          ...previous,
          {
            requestId: queryId || identity?.requestId || "",
            event: "answer.completed",
            message: "Answer ready",
            elapsedMs: typeof data.total_ms === "number" ? data.total_ms : undefined,
            metadata:
              typeof data.num_results === "number"
                ? { num_results: data.num_results }
                : undefined,
          },
        ]);
      } else if (event === "error") {
        throw new Error(sanitizeActivityMessage(data.message, "request.failed"));
      }
    }
  }

  setStatus("complete");
  const response: AskResponse = {
    question,
    answer: fullText,
    chunks: [],
    num_results: numResults,
    query_id: queryId,
    sources: citations,
    answer_type: typeof donePayload.answer_type === "string"
      ? (donePayload.answer_type as AskResponse["answer_type"])
      : undefined,
    title: typeof donePayload.title === "string" ? donePayload.title : undefined,
    summary: typeof donePayload.summary === "string" ? donePayload.summary : undefined,
    content_markdown:
      typeof donePayload.content_markdown === "string"
        ? donePayload.content_markdown
        : fullText,
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
  return {
    id: assistantId,
    role: "assistant",
    text: fullText,
    citations: citations.length > 0 ? citations : undefined,
    structured,
    confidence: structured.confidence,
    timestamp: new Date(),
    runId: identity?.runId,
  };
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
  return value.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const citation = item as Record<string, unknown>;
    if (
      typeof citation.id !== "string" ||
      typeof citation.title !== "string" ||
      typeof citation.url !== "string"
    ) return [];
    return [{
      id: citation.id,
      title: citation.title,
      url: citation.url,
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
  if (/fetch|network|connect|load failed/i.test(text)) {
    return "AskMcNeese is currently unreachable. Check your connection and try again.";
  }
  if (/request failed \(\d+\)/i.test(text)) {
    return "I couldn’t complete that request. Please try again.";
  }
  return "I couldn’t complete that request. Please try again.";
}
