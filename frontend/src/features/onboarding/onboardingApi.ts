import { getApiBase } from "../../lib/api";

export type OnboardingMode = "mandatory" | "optional" | "disabled";
export type TourStatus = "not_started" | "in_progress" | "completed";

export interface GuestTourState {
  version: number;
  status: TourStatus;
  currentStep: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
}

export interface GuestSession {
  guestId: string;
  displayAlias: string;
  isNewAssignment?: boolean;
  onboardingMode: OnboardingMode;
  tour: GuestTourState;
}

async function guestFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(
      response.status === 401
        ? "Guest session required."
        : `Onboarding request failed (${response.status}).`,
    );
  }
  const payload = (await response.json()) as { data: T };
  return payload.data;
}

export function bootstrapGuest(signal?: AbortSignal): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/bootstrap", { method: "POST", signal });
}

export function persistTourStep(step: string, version = 1): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/tour", {
    // The backend keeps PATCH for API clients, but browsers use the POST alias.
    // This survives stale gateways and cached preflight policies that omit PATCH.
    method: "POST",
    body: JSON.stringify({ version, step }),
  });
}

export async function completeTour(): Promise<GuestSession> {
  // Completion is a backend-validated transition. Explicitly confirm the
  // prerequisite first so a fast final click cannot outrun the progress queue.
  await persistTourStep("feedback");
  return persistTourStep("complete");
}

export function replayTour(): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/tour/replay", { method: "POST" });
}

export function resetTourDev(): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/dev-reset", { method: "POST" });
}
