import { describe, expect, it } from "vitest";
import { createAskRun, shouldShowLiveActivity } from "./lib/askRun";

/**
 * Guards the regression where persisting a conversation mid-ask wiped
 * activeRun / provisional assistant and hid live activity completely.
 */
describe("live activity visibility contract", () => {
  it("shows live activity for a running run even before SSE stages arrive", () => {
    const run = {
      ...createAskRun({
        runId: "run-1",
        requestId: "req-1",
        turnId: "turn-1",
        userMessageId: "u-1",
        assistantMessageId: "a-1",
      }),
      status: "running" as const,
    };
    expect(run.stages).toEqual([]);
    expect(shouldShowLiveActivity(run)).toBe(true);
  });
});
