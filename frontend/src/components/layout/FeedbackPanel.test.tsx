import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { FeedbackPanel } from "./FeedbackPanel";

const { submitGoogleFormFeedback } = vi.hoisted(() => ({
  submitGoogleFormFeedback: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../features/feedback/googleForm", () => ({
  getGoogleFeedbackConfig: () => ({
    actionUrl: "https://docs.google.com/forms/d/e/FORM_ID/formResponse",
    categoryEntry: "entry.123",
    messageEntry: "entry.456",
  }),
  submitGoogleFormFeedback,
}));

describe("FeedbackPanel", () => {
  it("keeps submit actionable and explains short feedback", () => {
    render(
      <MemoryRouter>
        <FeedbackPanel />
      </MemoryRouter>,
    );

    const submit = screen.getByRole("button", { name: "Submit" });
    const message = screen.getByRole("textbox", { name: /What happened/i });
    expect(submit).toBeEnabled();

    fireEvent.change(message, { target: { value: "Too short" } });
    fireEvent.submit(submit.closest("form") as HTMLFormElement);
    expect(screen.getByRole("alert")).toHaveTextContent(/at least 10 characters/i);
    expect(submitGoogleFormFeedback).not.toHaveBeenCalled();
  });

  it("submits the selected category and message", async () => {
    render(
      <MemoryRouter>
        <FeedbackPanel />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByRole("textbox", { name: /What happened/i }), {
      target: { value: "The answer linked to the wrong campus office." },
    });
    fireEvent.click(screen.getByLabelText("Missing information"));
    fireEvent.submit(screen.getByRole("button", { name: "Submit" }).closest("form") as HTMLFormElement);

    await waitFor(() =>
      expect(submitGoogleFormFeedback).toHaveBeenCalledWith(
        expect.any(Object),
        "Missing information",
        "The answer linked to the wrong campus office.",
      ),
    );
    expect(screen.getByText("Feedback sent")).toBeInTheDocument();
  });
});
