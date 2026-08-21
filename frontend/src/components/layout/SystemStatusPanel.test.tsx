import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { SystemStatusPanel } from "./SystemStatusPanel";

vi.mock("../../features/onboarding", () => ({
  useTour: () => ({
    guestAlias: "Guest TEST-1234",
    guestUsage: {
      questionsUsed: 3,
      questionLimit: 10,
      questionsRemaining: 7,
    },
  }),
}));

vi.mock("../../lib/api", () => ({
  fetchHealth: vi.fn().mockResolvedValue({ status: "ok" }),
}));

describe("SystemStatusPanel", () => {
  it("presents allowance, service state, and counting rules clearly", async () => {
    render(
      <MemoryRouter>
        <SystemStatusPanel />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: /Your beta allowance/i })).toBeInTheDocument();
    expect(screen.getByText("Guest TEST-1234")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: /3 of 10 beta questions used/i })).toHaveAttribute(
      "aria-valuenow",
      "3",
    );
    expect(await screen.findByRole("heading", { name: "AskMcNeese is ready" })).toBeInTheDocument();
    expect(screen.getByText(/Clearing conversation history does not reset/i)).toBeInTheDocument();
  });
});
