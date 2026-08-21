import { describe, expect, it } from "vitest";
import {
  applyActivityEvent,
  completeAskRun,
  createAskRun,
  type AskRun,
} from "./askRun";
import { buildResearchNarration, timeoutFallbackDetail } from "./researchPresentation";
import type { ActivityEvent } from "../types";

function ev(
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

function base(): AskRun {
  return createAskRun({
    requestId: "req-1",
    runId: "run-1",
    turnId: "turn-1",
    userMessageId: "u-1",
    assistantMessageId: "a-1",
  });
}

describe("researchPresentation", () => {
  it("empty run shows Starting your request", () => {
    const narration = buildResearchNarration({ ...base(), status: "running" });
    expect(narration.currentLabel).toBe("Starting your request");
    expect(narration.evidence).toHaveLength(0);
    expect(timeoutFallbackDetail(narration, 3000, false)).toBe(
      "Connecting to the server",
    );
  });

  it("real activity replaces understand timeout fallback copy", () => {
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev("query.analyzing", { phase: "understand" }, "Understanding what you need"),
    );
    let narration = buildResearchNarration(run);
    expect(timeoutFallbackDetail(narration, 3000, true)).toBe(
      "Choosing the best McNeese sources",
    );

    run = applyActivityEvent(
      run,
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    narration = buildResearchNarration(run);
    expect(narration.currentLabel).toBe("Searching trusted McNeese sources");
    expect(timeoutFallbackDetail(narration, 1000, true)).toBeUndefined();
  });

  it("search quiet gap shows still-searching fallback without completing a phase", () => {
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    const narration = buildResearchNarration(run);
    expect(timeoutFallbackDetail(narration, 4000, true)).toBe(
      "Still searching approved sources",
    );
    expect(narration.result).toBe("active");
  });

  it("repeated source_found events update one search narration and dedupe sources", () => {
    let run = base();
    run = applyActivityEvent(
      run,
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    run = applyActivityEvent(
      run,
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "Academic Calendar 2026–27",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/calendar",
          source_type: "official",
        },
        "Reading a relevant source",
      ),
    );
    run = applyActivityEvent(
      run,
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "Academic Calendar 2026–27",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/calendar",
          source_type: "official",
        },
        "Reading a relevant source",
      ),
    );
    run = applyActivityEvent(
      run,
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "International Student Services",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/international",
          source_type: "official",
        },
        "Reading a relevant source",
      ),
    );
    run = { ...run, status: "running" };
    const narration = buildResearchNarration(run);
    expect(narration.currentLabel).toBe("Reading relevant McNeese sources");
    expect(narration.evidence).toHaveLength(2);
    expect(narration.evidence.map((e) => e.title)).toEqual([
      "Academic Calendar 2026–27",
      "International Student Services",
    ]);
    expect(narration.history.filter((h) => h.label.includes("Academic")).length).toBe(0);
  });

  it("parallel operations do not complete one another", () => {
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev(
        "skill.started",
        { phase: "search", operation_id: "op-a", skill: "web" },
        "Searching official websites",
      ),
    );
    run = applyActivityEvent(
      run,
      ev(
        "skill.started",
        { phase: "search", operation_id: "op-b", skill: "kb" },
        "Searching the knowledge base",
      ),
    );
    const active = run.stages.filter((s) => s.status === "active");
    expect(active.length).toBeGreaterThanOrEqual(2);
    expect(active.map((s) => s.operationId).sort()).toEqual(["op-a", "op-b"]);
  });

  it("first answer chunk / streaming switches to compact write state", () => {
    let run = applyActivityEvent(
      base(),
      ev("answer.generating", { phase: "compose" }, "Writing your answer"),
    );
    run = { ...run, status: "streaming" };
    const narration = buildResearchNarration(run);
    expect(narration.compact).toBe(true);
    expect(narration.currentLabel).toBe("Writing your answer");
    expect(narration.evidence).toHaveLength(0);
  });

  it("completed run collapses to a quiet summary", () => {
    let run = applyActivityEvent(
      base(),
      ev("answer.generating", { phase: "compose" }, "Writing your answer"),
    );
    run = completeAskRun(run, "completed");
    const narration = buildResearchNarration(run);
    expect(narration.result).toBe("completed");
    expect(narration.completedTitle.toLowerCase()).toContain("research complete");
  });

  it("failed and cancelled results are distinct", () => {
    const failed = buildResearchNarration(completeAskRun(base(), "failed"));
    const cancelled = buildResearchNarration(completeAskRun(base(), "cancelled"));
    expect(failed.result).toBe("failed");
    expect(cancelled.result).toBe("cancelled");
  });

  it("announce key ignores source reel churn", () => {
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    const first = buildResearchNarration(run).announceKey;
    run = applyActivityEvent(
      run,
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "A",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/a",
        },
        "Reading a relevant source",
      ),
    );
    run = applyActivityEvent(
      run,
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "B",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/b",
        },
        "Reading a relevant source",
      ),
    );
    const second = buildResearchNarration(run);
    // Category stays search; label may shift to reading sources once, then stay stable.
    expect(second.announceKey.includes("search")).toBe(true);
    expect(second.announceText.toLowerCase()).not.toContain("https://");
    expect(first.startsWith("search|")).toBe(true);
  });
});
