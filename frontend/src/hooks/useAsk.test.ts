import { afterEach, describe, expect, it, vi } from "vitest";
import { useAsk } from "../hooks/useAsk";
import { act, renderHook } from "@testing-library/react";

function sseBody(frames: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const frame of frames) {
        controller.enqueue(encoder.encode(frame));
      }
      controller.close();
    },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useAsk error and abort contract", () => {
  it("returns an error assistant message on fetch rejection and ends loading", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    const { result } = renderHook(() => useAsk());
    let message = null;
    await act(async () => {
      message = await result.current.ask("What is the deadline?");
    });
    expect(message?.isError).toBe(true);
    expect(message?.text).toMatch(/unreachable|try again/i);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeTruthy();
    expect(result.current.status).toBe("error");
  });

  it("returns an error message on HTTP failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        body: null,
      }),
    );
    const { result } = renderHook(() => useAsk());
    let message = null;
    await act(async () => {
      message = await result.current.ask("Help");
    });
    expect(message?.isError).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it("returns null on abort without setting a false error", async () => {
    let abortSignal: AbortSignal | null = null;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
        abortSignal = init?.signal ?? null;
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            const err = new Error("Aborted");
            err.name = "AbortError";
            reject(err);
          });
        });
      }),
    );
    const { result } = renderHook(() => useAsk());
    let message: Awaited<ReturnType<typeof result.current.ask>> = null;
    await act(async () => {
      const pending = result.current.ask("Long question");
      result.current.stop();
      message = await pending;
    });
    expect(abortSignal?.aborted).toBe(true);
    expect(message).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.status).toBe("stopped");
  });

  it("clears a stale error when a new ask begins", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce({
        ok: true,
        body: sseBody([
          'event: done\ndata: {"query_id":"q1","num_results":0,"answer":"Hi","answer_type":"conversational"}\n\n',
        ]),
      });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAsk());
    await act(async () => {
      await result.current.ask("fail first");
    });
    expect(result.current.error).toBeTruthy();

    await act(async () => {
      await result.current.ask("ok second");
    });
    expect(result.current.error).toBeNull();
    expect(result.current.status).toBe("complete");
  });
});

describe("useAsk request visual lifecycle", () => {
  it("sends task selection state and preserves the authoritative final state", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: sseBody([
        'event: done\ndata: {"query_id":"q-task","num_results":0,"content_markdown":"Choose a CRN","task_state":{"schema_version":1,"task_type":"course_schedule_conflict","status":"awaiting_input","pending_field":"constraint_section"},"release_decision":{"status":"CAN_RELEASE","reasons":[],"evidence_passed":false,"partial_allowed":false},"claim_ledger":[]}\n\n',
      ]),
    });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAsk());
    let message: Awaited<ReturnType<typeof result.current.ask>> = null;
    const taskState = {
      schema_version: 1 as const,
      task_type: "course_schedule_conflict",
      status: "awaiting_input" as const,
      term: "Fall 2026",
      subject: "CSCI",
      constraint_course: "MATH 291",
    };
    await act(async () => {
      message = await result.current.ask(
        "61066",
        "adaptive",
        undefined,
        undefined,
        undefined,
        undefined,
        taskState,
      );
    });
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    const body = JSON.parse(String(request.body));
    expect(body.task_state).toEqual(taskState);
    expect(message?.taskState?.pending_field).toBe("constraint_section");
    expect(message?.releaseDecision?.status).toBe("CAN_RELEASE");
  });

  it("marks submitting then streaming, and returns to idle after the answer is built", async () => {
    let releaseFetch!: (value: {
      ok: boolean;
      body: ReadableStream<Uint8Array>;
    }) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        () =>
          new Promise((resolve) => {
            releaseFetch = resolve;
          }),
      ),
    );

    const { result } = renderHook(() => useAsk());
    expect(result.current.requestVisualState).toEqual({
      requestId: 0,
      phase: "idle",
    });

    let pending!: Promise<unknown>;
    await act(async () => {
      pending = result.current.ask("Hello?");
    });
    expect(result.current.requestVisualState.phase).toBe("submitting");
    expect(result.current.requestVisualState.requestId).toBeGreaterThan(0);
    const activeRequestId = result.current.requestVisualState.requestId;

    await act(async () => {
      releaseFetch({
        ok: true,
        body: sseBody([
          'event: chunk\ndata: {"text":"Hello"}\n\n',
          'event: done\ndata: {"query_id":"q1","num_results":0,"answer":"Hello","content_markdown":"Hello","answer_type":"conversational"}\n\n',
        ]),
      });
      await pending;
    });

    expect(result.current.requestVisualState).toEqual({
      requestId: activeRequestId,
      phase: "idle",
    });
  });

  it("prefers done.content_markdown over partial stream chunks", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        body: sseBody([
          'event: chunk\ndata: {"text":"Partial…"}\n\n',
          'event: done\ndata: {"query_id":"q2","num_results":1,"content_markdown":"Full authentic answer from sources.","answer_type":"factual"}\n\n',
        ]),
      }),
    );

    const { result } = renderHook(() => useAsk());
    let message: Awaited<ReturnType<typeof result.current.ask>> = null;
    await act(async () => {
      message = await result.current.ask("Who is the president?");
    });

    expect(message?.text).toBe("Full authentic answer from sources.");
    expect(message?.structured?.contentMarkdown).toBe(
      "Full authentic answer from sources.",
    );
  });

  it("ignores replayed SSE frames with the same event id", async () => {
    const duplicate = 'event: chunk\ndata: {"event_id":"evt-1","request_id":"req-1","turn_id":"turn-1","text":"Hello"}\n\n';
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        body: sseBody([
          duplicate,
          duplicate,
          'event: done\ndata: {"event_id":"evt-2","request_id":"req-1","turn_id":"turn-1","query_id":"req-1","num_results":0,"content_markdown":"Hello"}\n\n',
        ]),
      }),
    );

    const { result } = renderHook(() => useAsk());
    let message: Awaited<ReturnType<typeof result.current.ask>> = null;
    await act(async () => {
      message = await result.current.ask(
        "Hi",
        "adaptive",
        undefined,
        undefined,
        {
          requestId: "req-1",
          turnId: "turn-1",
          assistantMessageId: "a-1",
          runId: "run-1",
        },
      );
    });
    expect(message?.text).toBe("Hello");
  });

  it("clears the visual phase immediately on stop", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            const err = new Error("Aborted");
            err.name = "AbortError";
            reject(err);
          });
        });
      }),
    );

    const { result } = renderHook(() => useAsk());
    let pending!: Promise<unknown>;
    await act(async () => {
      pending = result.current.ask("Long question");
    });
    expect(result.current.requestVisualState.phase).toBe("submitting");

    await act(async () => {
      result.current.stop();
      await pending;
    });
    expect(result.current.requestVisualState.phase).toBe("idle");
  });
});
