import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LiveAnswerProgress } from "./components/chat/LiveAnswerProgress";
import {
  applyActivityEvent,
  completeAskRun,
  createAskRun,
  type AskRun,
} from "./lib/askRun";
import type { ActivityEvent } from "./types";

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

describe("minimal live research trail UI", () => {
  it("renders starting request with no card, rail, or nested action box", () => {
    const { container } = render(
      <LiveAnswerProgress run={{ ...base(), status: "running" }} />,
    );
    expect(screen.getAllByText(/Starting your request/i).length).toBeGreaterThan(0);
    expect(container.querySelector(".researchTrail")).toBeTruthy();
    expect(container.querySelector(".liveTrail")).toBeNull();
    expect(container.querySelector(".liveTrailRail")).toBeNull();
    expect(container.querySelector(".liveTrailCurrent")).toBeNull();
    expect(screen.queryByText(/^Understand$/)).toBeNull();
    expect(screen.queryByText(/^Verify$/)).toBeNull();
    expect(screen.queryByText(/step/i)).toBeNull();
    expect(screen.queryByText(/%/)).toBeNull();
  });

  it("announces category changes once via a single status region", () => {
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    const { container } = render(<LiveAnswerProgress run={run} />);
    const statuses = container.querySelectorAll('[role="status"]');
    expect(statuses).toHaveLength(1);
    expect(statuses[0]).toHaveTextContent(/Searching trusted McNeese sources/i);
    // Source reel is aria-hidden when present; absent when empty.
    const sources = container.querySelector(".researchTrailSources");
    if (sources) {
      expect(sources).toHaveAttribute("aria-hidden", "true");
    }
  });

  it("collapses completed run and expands activity on demand", async () => {
    const user = userEvent.setup();
    let run = applyActivityEvent(
      base(),
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    run = completeAskRun(run, "completed");
    render(<LiveAnswerProgress run={run} />);
    expect(screen.getByTestId("research-trail-completed")).toBeInTheDocument();
    expect(screen.getByText(/Research complete/i)).toBeInTheDocument();
    const toggle = screen.getByRole("button", { name: /Expand activity/i });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });

  it("keeps stopped runs visible with stop copy", () => {
    const run = completeAskRun(
      applyActivityEvent(
        { ...base(), status: "running" },
        ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
      ),
      "cancelled",
    );
    render(<LiveAnswerProgress run={run} />);
    expect(screen.getByText(/Research stopped/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Expand activity/i })).toBeInTheDocument();
  });

  it("failed run uses failure copy without a phase rail", () => {
    const run = completeAskRun(
      applyActivityEvent(
        { ...base(), status: "running" },
        ev("request.failed", { phase: "search" }, "The request could not finish"),
      ),
      "failed",
    );
    const { container } = render(<LiveAnswerProgress run={run} />);
    expect(screen.getByText(/Search could not finish/i)).toBeInTheDocument();
    expect(container.querySelector(".liveTrailRail")).toBeNull();
    expect(container.querySelector(".researchTrailGlyphFail")).toBeTruthy();
  });

  it("uses McNeese blue live tone then gold write tone on the status glyph", () => {
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    const { container, rerender } = render(<LiveAnswerProgress run={run} />);
    expect(container.querySelector(".researchTrailGlyph")?.getAttribute("data-tone")).toBe(
      "live",
    );

    run = applyActivityEvent(
      run,
      ev("answer.generating", { phase: "compose" }, "Writing your answer"),
    );
    run = { ...run, status: "streaming" };
    rerender(<LiveAnswerProgress run={run} />);
    expect(container.querySelector(".researchTrailGlyph")?.getAttribute("data-tone")).toBe(
      "write",
    );
  });

  it("compact write state hides source reel", () => {
    let run = applyActivityEvent(
      base(),
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "Academic Calendar 2026–27",
          source_host: "mcneese.edu",
          source_url: "https://www.mcneese.edu/calendar",
        },
        "Reading a relevant source",
      ),
    );
    run = applyActivityEvent(
      run,
      ev("answer.generating", { phase: "compose" }, "Writing your answer"),
    );
    run = { ...run, status: "streaming" };
    const { container } = render(<LiveAnswerProgress run={run} />);
    expect(screen.getAllByText(/Writing your answer/i).length).toBeGreaterThan(0);
    expect(container.querySelector(".researchTrail")).toHaveAttribute(
      "data-compact",
      "true",
    );
    expect(screen.queryByText(/Academic Calendar/i)).not.toBeInTheDocument();
  });

  it("does not call smooth scroll helpers from the trail itself", () => {
    const scrollTo = vi.fn();
    Object.defineProperty(window, "scrollTo", { value: scrollTo, writable: true });
    let run = applyActivityEvent(
      { ...base(), status: "running" },
      ev("retrieval.started", { phase: "search" }, "Searching trusted McNeese sources"),
    );
    const { rerender } = render(<LiveAnswerProgress run={run} />);
    run = applyActivityEvent(
      run,
      ev(
        "retrieval.source_found",
        {
          phase: "search",
          kind: "evidence",
          source_title: "A",
          source_url: "https://www.mcneese.edu/a",
        },
        "Reading a relevant source",
      ),
    );
    rerender(<LiveAnswerProgress run={run} />);
    expect(scrollTo).not.toHaveBeenCalled();
  });
});
