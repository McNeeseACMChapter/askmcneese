import { afterEach, describe, expect, it, vi } from "vitest";
import { bootstrapGuest, completeTour, persistTourStep, skipTour, type GuestSession } from "./onboardingApi";

const session: GuestSession = {
  guestId: "guest_test",
  displayAlias: "Guest A1B2-C3D4-E5F6",
  onboardingMode: "mandatory",
  usage: { questionsUsed: 0, questionLimit: 10, questionsRemaining: 10 },
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
  localStorage.clear();
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

  it("stores the cross-origin token and sends it on later writes", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { ...session, guestToken: "raw-browser-token" } }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: session }) });
    vi.stubGlobal("fetch", fetchMock);

    await bootstrapGuest();
    await persistTourStep("welcome");

    expect(localStorage.getItem("askmcneese_guest_token")).toBe("raw-browser-token");
    expect(fetchMock.mock.calls[1]?.[1]?.headers).toMatchObject({
      "X-Guest-Token": "raw-browser-token",
    });
  });

  it("coalesces simultaneous first-load bootstrap requests into one identity", async () => {
    let resolveBootstrap!: (value: unknown) => void;
    const fetchMock = vi.fn().mockReturnValue(new Promise((resolve) => {
      resolveBootstrap = resolve;
    }));
    vi.stubGlobal("fetch", fetchMock);

    const first = bootstrapGuest();
    const second = bootstrapGuest();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    resolveBootstrap({
      ok: true,
      json: async () => ({ data: { ...session, guestToken: "one-browser-token" } }),
    });
    await expect(first).resolves.toMatchObject({ guestId: session.guestId });
    await expect(second).resolves.toMatchObject({ guestId: session.guestId });
  });

  it("recovers once from an expired guest token before retrying the write", async () => {
    localStorage.setItem("askmcneese_guest_token", "expired-token");
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 401 })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { ...session, guestToken: "replacement-token" } }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: session }) });
    vi.stubGlobal("fetch", fetchMock);

    await persistTourStep("welcome");

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(String(fetchMock.mock.calls[1]?.[0])).toContain("/guest/bootstrap");
    expect(fetchMock.mock.calls[2]?.[1]?.headers).toMatchObject({
      "X-Guest-Token": "replacement-token",
    });
  });

  it("persists the explicit skip action", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    await skipTour();

    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("/guest/tour/skip");
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ method: "POST" });
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
