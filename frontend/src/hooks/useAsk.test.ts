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
