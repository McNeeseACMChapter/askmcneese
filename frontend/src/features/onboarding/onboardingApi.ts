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

export interface GuestUsage {
  questionsUsed: number;
  questionLimit: number;
  questionsRemaining: number;
}

export interface GuestSession {
  guestId: string;
  displayAlias: string;
  guestToken?: string;
  isNewAssignment?: boolean;
  onboardingMode: OnboardingMode;
  tour: GuestTourState;
  usage: GuestUsage;
}

const TOKEN_STORAGE_KEY = "askmcneese_guest_token";
let bootstrapInFlight: Promise<GuestSession> | null = null;

export function getGuestToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function rememberGuestToken(session: GuestSession): void {
  if (!session.guestToken) return;
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, session.guestToken);
  } catch {
    // Cookie persistence still works in same-site deployments.
  }
}

async function requestGuest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getGuestToken();
  const response = await fetch(getApiBase() + path, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { "X-Guest-Token": token } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const message = response.status === 401
      ? "Guest session required."
      : response.status === 429
        ? "This beta guest has reached the question limit."
        : "Onboarding request failed (" + response.status + ").";
    const error = new Error(message) as Error & { status?: number };
    error.status = response.status;
    throw error;
  }
  const payload = (await response.json()) as { data: T };
  const session = payload.data as GuestSession;
  if (session?.guestId) rememberGuestToken(session);
  return payload.data;
}

async function recoverGuest(): Promise<GuestSession> {
  if (!bootstrapInFlight) {
    bootstrapInFlight = requestGuest<GuestSession>("/guest/bootstrap", { method: "POST" })
      .finally(() => {
        bootstrapInFlight = null;
      });
  }
  return bootstrapInFlight;
}

async function guestFetch<T>(
  path: string,
  init?: RequestInit,
  recoverOnUnauthorized = true,
): Promise<T> {
  try {
    return await requestGuest<T>(path, init);
  } catch (error) {
    const status = (error as Error & { status?: number }).status;
    if (status !== 401 || !recoverOnUnauthorized || path === "/guest/bootstrap") throw error;
    await recoverGuest();
    return requestGuest<T>(path, init);
  }
}

export function bootstrapGuest(signal?: AbortSignal): Promise<GuestSession> {
  // A first render can be mounted twice by React StrictMode before the browser
  // has received and stored its server-issued token. Share that first request
  // so one browser profile cannot accidentally mint two competing identities.
  if (!getGuestToken()) {
    if (!bootstrapInFlight) {
      bootstrapInFlight = requestGuest<GuestSession>("/guest/bootstrap", { method: "POST" })
        .finally(() => {
          bootstrapInFlight = null;
        });
    }
    return bootstrapInFlight;
  }
  return requestGuest<GuestSession>("/guest/bootstrap", { method: "POST", signal });
}

export function persistTourStep(step: string, version = 1): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/tour", {
    method: "POST",
    body: JSON.stringify({ version, step }),
  });
}

export async function completeTour(): Promise<GuestSession> {
  await persistTourStep("feedback");
  return persistTourStep("complete");
}

export function skipTour(): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/tour/skip", { method: "POST" });
}

export function replayTour(): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/tour/replay", { method: "POST" });
}

export interface FeedbackReceipt {
  id: number;
  category: string;
  createdAt: string;
}

export function submitGuestFeedback(
  category: string,
  message: string,
  pageUrl?: string,
): Promise<FeedbackReceipt> {
  return guestFetch<FeedbackReceipt>("/guest/feedback", {
    method: "POST",
    body: JSON.stringify({ category, message, pageUrl }),
  });
}
export function resetTourDev(): Promise<GuestSession> {
  return guestFetch<GuestSession>("/guest/dev-reset", { method: "POST" });
}
