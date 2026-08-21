import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getGoogleFeedbackConfig,
  submitGoogleFormFeedback,
} from "./googleForm";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Google Forms feedback transport", () => {
  it("uses the public AskMcNeese form when no override is configured", () => {
    expect(getGoogleFeedbackConfig({})).toEqual({
      actionUrl:
        "https://docs.google.com/forms/d/e/1FAIpQLSdBnSo7B1NGrm5DRYGJnMfvfqL1Q10u1GNeJQXK0GMvJNCBcg/formResponse",
      categoryEntry: "entry.516755088",
      messageEntry: "entry.1067231505",
    });
  });

  it("requires a Google formResponse URL and two entry IDs", () => {
    expect(
      getGoogleFeedbackConfig({
        VITE_GOOGLE_FEEDBACK_FORM_ACTION:
          "https://docs.google.com/forms/d/e/FORM_ID/formResponse",
        VITE_GOOGLE_FEEDBACK_CATEGORY_ENTRY: "entry.123",
        VITE_GOOGLE_FEEDBACK_MESSAGE_ENTRY: "entry.456",
      }),
    ).toEqual({
      actionUrl: "https://docs.google.com/forms/d/e/FORM_ID/formResponse",
      categoryEntry: "entry.123",
      messageEntry: "entry.456",
    });

    expect(
      getGoogleFeedbackConfig({
        VITE_GOOGLE_FEEDBACK_FORM_ACTION: "https://example.com/collect",
        VITE_GOOGLE_FEEDBACK_CATEGORY_ENTRY: "category",
        VITE_GOOGLE_FEEDBACK_MESSAGE_ENTRY: "message",
      }),
    ).toBeNull();
  });

  it("posts only category and message without credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response());

    await submitGoogleFormFeedback(
      {
        actionUrl: "https://docs.google.com/forms/d/e/FORM_ID/formResponse",
        categoryEntry: "entry.123",
        messageEntry: "entry.456",
      },
      "Incorrect answer",
      "The answer cited the wrong office.",
    );

    expect(fetchMock).toHaveBeenCalledOnce();
    const [, request] = fetchMock.mock.calls[0];
    expect(request).toMatchObject({
      method: "POST",
      mode: "no-cors",
      credentials: "omit",
      referrerPolicy: "no-referrer",
    });
    expect(String(request?.body)).toBe(
      "entry.123=Incorrect+answer&entry.456=The+answer+cited+the+wrong+office.",
    );
  });
});
