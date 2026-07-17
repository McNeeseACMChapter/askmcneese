import { describe, expect, it } from "vitest";
import {
  applyActivityEvent,
  completeAskRun,
  completedRunHeadline,
  createAskRun,
  shouldShowLiveActivity,
} from "./askRun";
import type { ActivityEvent } from "../types";

function event(
  requestId: string,
  partial: Partial<ActivityEvent> & Pick<ActivityEvent, "event" | "message">,
): ActivityEvent {
  return {
    requestId,
    ...partial,
  };
}

describe("askRun ownership", () => {
  it("creates an isolated run with empty stages", () => {
    const run = createAskRun({
      runId: "run-1",
      requestId: "req-1",
      turnId: "turn-1",
      userMessageId: "u-1",
      assistantMessageId: "a-1",
    });
    expect(run.stages).toEqual([]);
    expect(run.status).toBe("queued");
    expect(shouldShowLiveActivity(run)).toBe(true);
  });

  it("routes activity into one run and completes prior active stage", () => {
    let run = createAskRun({
      runId: "run-2",
      requestId: "req-2",
      turnId: "turn-2",
      userMessageId: "u-2",
      assistantMessageId: "a-2",
    });
    run = applyActivityEvent(
      run,
      event("req-2", {
        event: "query.analyzing",
        message: "Reading your question to decide what to search",
      }),
    );
    run = applyActivityEvent(
      run,
      event("req-2", {
        event: "retrieval.started",
        message: "Searching approved McNeese websites…",
        metadata: { skill: "official_web", sources_found: 0 },
      }),
    );
    expect(run.stages).toHaveLength(2);
    expect(run.stages[0].status).toBe("completed");
    expect(run.stages[1].status).toBe("active");
    expect(run.stages[1].label).toContain("Searching approved");
  });

  it("rejects duplicate consecutive events", () => {
    let run = createAskRun({
      runId: "run-3",
      requestId: "req-3",
      turnId: "turn-3",
      userMessageId: "u-3",
      assistantMessageId: "a-3",
    });
    const same = event("req-3", {
      event: "retrieval.source_found",
      message: "Found 3 useful sources so far",
      metadata: { sources_found: 3 },
    });
    run = applyActivityEvent(run, same);
    run = applyActivityEvent(run, same);
    expect(run.stages).toHaveLength(1);
    expect(run.sourcesFound).toBe(3);
  });

  it("does not share stages across runs", () => {
    let runA = createAskRun({
      runId: "run-a",
      requestId: "req-a",
      turnId: "turn-a",
      userMessageId: "u-a",
      assistantMessageId: "a-a",
    });
    const runB = createAskRun({
      runId: "run-b",
      requestId: "req-b",
      turnId: "turn-b",
      userMessageId: "u-b",
      assistantMessageId: "a-b",
    });
    runA = applyActivityEvent(
      runA,
      event("req-a", {
        event: "retrieval.started",
        message: "Searching the McNeese knowledge base…",
      }),
    );
    expect(runA.stages).toHaveLength(1);
    expect(runB.stages).toHaveLength(0);
  });

  it("rejects events for a different request id", () => {
    const run = createAskRun({
      runId: "run-x",
      requestId: "req-x",
      turnId: "turn-x",
      userMessageId: "u-x",
      assistantMessageId: "a-x",
    });
    const next = applyActivityEvent(
      run,
      event("other-req", {
        event: "retrieval.started",
        message: "Should not attach",
      }),
    );
    expect(next.stages).toHaveLength(0);
    expect(next).toBe(run);
  });

  it("preserves an old run when a new run is created", () => {
    let runA = createAskRun({
      runId: "run-a2",
      requestId: "req-a2",
      turnId: "turn-a2",
      userMessageId: "u-a2",
      assistantMessageId: "a-a2",
    });
    runA = applyActivityEvent(
      runA,
      event("req-a2", {
        event: "retrieval.completed",
        message: "Finished collecting sources",
        metadata: { sources_found: 4 },
      }),
    );
    const finishedA = completeAskRun(runA);
    const runB = createAskRun({
      runId: "run-b2",
      requestId: "req-b2",
      turnId: "turn-b2",
      userMessageId: "u-b2",
      assistantMessageId: "a-b2",
    });
    expect(finishedA.stages).toHaveLength(1);
    expect(finishedA.status).toBe("completed");
    expect(runB.stages).toHaveLength(0);
    expect(runB.status).toBe("queued");
  });

  it("marks completed runs without inventing stages", () => {
    const run = completeAskRun(
      createAskRun({
        runId: "run-c",
        requestId: "req-c",
        turnId: "turn-c",
        userMessageId: "u-c",
        assistantMessageId: "a-c",
      }),
      "completed",
    );
    expect(run.status).toBe("completed");
    expect(run.stages).toEqual([]);
    expect(shouldShowLiveActivity(run)).toBe(false);
  });

  it("builds a distinctive completed headline from stages", () => {
    let run = createAskRun({
      runId: "run-h",
      requestId: "req-h",
      turnId: "turn-h",
      userMessageId: "u-h",
      assistantMessageId: "a-h",
    });
    run = applyActivityEvent(
      run,
      event("req-h", {
        event: "retrieval.started",
        message: "Searching approved McNeese websites…",
        metadata: { skill: "official_web" },
      }),
    );
    run = applyActivityEvent(
      run,
      event("req-h", {
        event: "retrieval.completed",
        message: "Finished collecting sources (4 total)",
        metadata: { sources_found: 4, source_preview: "Admissions · Aid" },
      }),
    );
    run = completeAskRun(run, "completed");
    expect(completedRunHeadline(run)).toBe("Campus live · 4 sources");
  });
});
