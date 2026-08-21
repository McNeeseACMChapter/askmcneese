import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { LiveAnswerProgress } from "./components/chat/LiveAnswerProgress";
import { applyActivityEvent, createAskRun } from "./lib/askRun";

describe("reduced motion live progress", () => {
  afterEach(() => {
    // no media mock cleanup required
  });

  it("exposes a single status region without a phase rail or card chrome", () => {
    let run = createAskRun({
      runId: "run-1",
      requestId: "r1",
      turnId: "t1",
      userMessageId: "u1",
      assistantMessageId: "a1",
    });
    run = applyActivityEvent(run, {
      requestId: "r1",
      runId: "run-1",
      event: "retrieval.started",
      message: "Searching trusted McNeese sources",
      metadata: { phase: "search", kind: "milestone" },
    });
    run = { ...run, status: "running" };

    const { container } = render(<LiveAnswerProgress run={run} />);
    expect(screen.getByLabelText(/Live research activity/i)).toHaveAttribute("aria-busy", "true");
    expect(screen.getAllByText(/Searching trusted McNeese sources/i).length).toBeGreaterThan(0);
    expect(container.querySelector(".researchTrail")).toBeTruthy();
    expect(container.querySelector(".liveTrailRail")).toBeNull();
    expect(container.querySelector(".liveTrailCurrentIcon")).toBeNull();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
