import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { LiveAnswerProgress } from "./components/chat/LiveAnswerProgress";
import { applyActivityEvent, createAskRun } from "./lib/askRun";

describe("reduced motion live progress", () => {
  afterEach(() => {
    // no media mock cleanup required
  });

  it("still exposes accessible progress without a blue pulse", () => {
    let run = createAskRun({
      runId: "run-1",
      requestId: "r1",
      turnId: "t1",
      userMessageId: "u1",
      assistantMessageId: "a1",
    });
    run = applyActivityEvent(run, {
      requestId: "r1",
      event: "retrieval.started",
      message: "Searching McNeese-approved sources",
    });
    run = { ...run, status: "running" };

    const { container } = render(<LiveAnswerProgress run={run} />);
    expect(screen.getByLabelText(/Live answer activity/i)).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText(/^Live$/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Searching McNeese-approved sources/i).length).toBeGreaterThan(0);
    expect(container.querySelector(".live-progress-dot")).toBeNull();
    expect(container.querySelector(".live-activity-icon")).toBeNull();
    expect(screen.queryByText(/Live progress/i)).not.toBeInTheDocument();
  });
});
