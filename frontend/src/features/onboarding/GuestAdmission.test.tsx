import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { GuestAdmission } from "./GuestAdmission";

afterEach(() => {
  vi.useRealTimers();
});

describe("GuestAdmission", () => {
  it("shows the stable guest identity and auto-starts after five seconds", () => {
    vi.useFakeTimers();
    const onStart = vi.fn();
    render(
      <GuestAdmission
        alias="Guest 1"
        mode="admission"
        onStart={onStart}
        onSkip={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "Guest 1" })).toBeInTheDocument();
    expect(screen.getByText("Walkthrough starts in 5 seconds")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start walkthrough" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Skip for now" })).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(5000));
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it("lets the guest skip immediately", () => {
    const onSkip = vi.fn();
    render(
      <GuestAdmission
        alias="Guest 1"
        mode="admission"
        onStart={vi.fn()}
        onSkip={onSkip}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Skip for now" }));
    expect(onSkip).toHaveBeenCalledTimes(1);
  });
});