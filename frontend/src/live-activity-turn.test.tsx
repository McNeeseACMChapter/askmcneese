import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { ChatPage } from "./components/chat/ChatPage";
import { createAskRun, applyActivityEvent } from "./lib/askRun";
import type { ChatMessage } from "./types";

describe("ChatPage turn-owned live activity", () => {
  it("renders run-2 only beside assistant-message-2", () => {
    const messages: ChatMessage[] = [
      { id: "u-1", role: "user", text: "First question?", timestamp: new Date() },
      {
        id: "a-1",
        role: "assistant",
        text: "First answer.",
        timestamp: new Date(),
        runSummary: {
          runId: "run-1",
          status: "completed",
          stages: [
            {
              id: "s1",
              event: "answer.completed",
              label: "Answer ready",
              status: "completed",
            },
          ],
          sourcesFound: 2,
        },
      },
      { id: "u-2", role: "user", text: "Second question?", timestamp: new Date() },
      {
        id: "a-2",
        role: "assistant",
        text: "",
        isStreaming: true,
        timestamp: new Date(),
        runId: "run-2",
      },
    ];

    let run2 = createAskRun({
      runId: "run-2",
      requestId: "req-2",
      turnId: "turn-2",
      userMessageId: "u-2",
      assistantMessageId: "a-2",
    });
    run2 = applyActivityEvent(run2, {
      requestId: "req-2",
      event: "retrieval.started",
      message: "Searching McNeese-approved campus sources",
    });

    const { container } = render(
      <MemoryRouter>
        <ChatPage
          messages={messages}
          isLoading
          askStatus="searching"
          activeRun={run2}
          offline={false}
          sourceScope="adaptive"
          onSend={vi.fn()}
          onStop={vi.fn()}
          onSourceScopeChange={vi.fn()}
        />
      </MemoryRouter>,
    );

    const turn1 = container.querySelector('[data-message-id="a-1"]');
    const turn2 = container.querySelector('[data-message-id="a-2"]');
    expect(turn1).toBeTruthy();
    expect(turn2).toBeTruthy();
    expect(turn2?.getAttribute("data-run-id")).toBe("run-2");
    expect(turn1?.textContent).not.toContain("Searching McNeese-approved campus sources");
    expect(turn2?.textContent).toContain("Searching McNeese-approved campus sources");
    expect(turn2?.textContent).toContain("Live");
    expect(screen.queryByText(/Live progress/i)).not.toBeInTheDocument();
  });
});
