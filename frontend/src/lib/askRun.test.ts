import { describe, expect, it } from "vitest";
import {
  applyActivityEvent,
  buildLiveTrail,
  createAskRun,
  type AskRun,
} from "./askRun";
import type { ActivityEvent } from "../types";

function event(
  name: string,
  metadata: Record<string, unknown> = {},
  message = name,
): ActivityEvent {
  return {
    requestId: "req-1",
    runId: "run-1",
    event: name,
    message,
    elapsedMs: 100,
    metadata: metadata as ActivityEvent["metadata"],
  };
}

function run(): AskRun {
  return createAskRun({
    requestId: "req-1",
    runId: "run-1",
    turnId: "turn-1",
    userMessageId: "u-1",
    assistantMessageId: "a-1",
  });
}

describe("AskRun live trail", () => {
  it("preserves parallel search operations", () => {
    let current = run();
    current = applyActivityEvent(
      current,
      event("skill.started", {
        phase: "search",
        kind: "operation",
        operation_id: "kb",
        skill: "kb_retrieve",
      }),
    );
    current = applyActivityEvent(
      current,
      event("skill.started", {
        phase: "search",
        kind: "operation",
        operation_id: "official",
        skill: "official_web",
      }),
    );

    expect(current.stages.filter((stage) => stage.status === "active")).toHaveLength(2);

    current = applyActivityEvent(
      current,
      event("skill.completed", {
        phase: "search",
        kind: "operation",
        operation_id: "kb",
        skill: "kb_retrieve",
        result_count: 5,
      }),
    );

    expect(current.stages.find((stage) => stage.operationId === "kb")?.status).toBe("completed");
    expect(current.stages.find((stage) => stage.operationId === "official")?.status).toBe("active");
  });

  it("deduplicates semantic repeats even when elapsed time changes", () => {
    const first = event("query.analyzing", { phase: "understand" }, "Understanding");
    const second = { ...first, elapsedMs: 900 };
    const once = applyActivityEvent(run(), first);
    const twice = applyActivityEvent(once, second);

    expect(twice.stages).toHaveLength(1);
  });

  it("keeps source evidence separate from pipeline milestones", () => {
    let current = run();
    current = applyActivityEvent(
      current,
      event("retrieval.source_found", {
        phase: "search",
        kind: "evidence",
        source_title: "Academic Calendar 2026–27",
        source_host: "mcneese.edu",
        source_url: "https://www.mcneese.edu/academics/calendar/",
        source_type: "official",
      }),
    );

    const trail = buildLiveTrail(current);
    expect(trail.evidence).toHaveLength(1);
    expect(trail.evidence[0]?.sourceTitle).toBe("Academic Calendar 2026–27");
  });

  it("assigns an unscoped failure to the phase that was running", () => {
    let current = run();
    current = applyActivityEvent(
      current,
      event("retrieval.started", { phase: "search" }),
    );
    current = applyActivityEvent(current, event("request.failed", {}, "Search failed"));

    const failed = current.stages[current.stages.length - 1];
    expect(failed?.phase).toBe("search");
    expect(buildLiveTrail(current).phases.find((phase) => phase.id === "search")?.status).toBe(
      "failed",
    );
    expect(buildLiveTrail(current).phases.find((phase) => phase.id === "compose")?.status).toBe(
      "pending",
    );
  });
});
