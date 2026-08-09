import { afterEach, describe, expect, it, vi } from "vitest";
import { completeTour, persistTourStep, type GuestSession } from "./onboardingApi";

const session: GuestSession = {
  guestId: "guest_test",
  displayAlias: "TEST",
  onboardingMode: "mandatory",
  tour: {
    version: 1,
    status: "in_progress",
    currentStep: "feedback",
  },
};

function successfulFetch() {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ data: session }),
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("onboardingApi", () => {
  it("uses the CORS-safe POST alias for browser progress writes", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    await persistTourStep("welcome");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      credentials: "include",
    });
  });

  it("confirms Feedback before sending the final completion transition", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    await completeTour();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({
      version: 1,
      step: "feedback",
    });
    expect(JSON.parse(String(fetchMock.mock.calls[1]?.[1]?.body))).toEqual({
      version: 1,
      step: "complete",
    });
  });
});
