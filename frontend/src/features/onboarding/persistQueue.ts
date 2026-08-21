import { persistTourStep, type GuestSession } from "./onboardingApi";

type PersistListener = (session: GuestSession | null, error: Error | null, final: boolean) => void;

/**
 * Single-flight, deduped tour progress writer with bounded exponential backoff.
 * Never loops forever; never storms identical PATCH calls.
 */
export class TourPersistQueue {
  private pending: string | null = null;
  private inFlight: string | null = null;
  private lastAcked: string | null = null;
  private attempts = 0;
  private timer: number | null = null;
  private closed = false;
  private readonly maxAttempts = 5;
  private readonly onUpdate: PersistListener;

  constructor(onUpdate: PersistListener) {
    this.onUpdate = onUpdate;
  }

  enqueue(step: string, isFinal = false) {
    if (this.closed) return;
    if (!isFinal && step === this.lastAcked) return;
    if (!isFinal && step === this.inFlight) return;
    if (!isFinal && step === this.pending && this.timer != null) return;
    this.pending = step;
    if (this.inFlight) return;
    void this.drain(isFinal);
  }

  dispose() {
    this.closed = true;
    if (this.timer != null) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
  }

  private async drain(isFinal: boolean) {
    if (this.closed || this.inFlight || !this.pending) return;
    const step = this.pending;
    this.pending = null;
    this.inFlight = step;
    try {
      const session = await persistTourStep(step);
      this.lastAcked = step;
      this.attempts = 0;
      this.inFlight = null;
      this.onUpdate(session, null, isFinal && step === "complete");
      if (this.pending) void this.drain(this.pending === "complete");
    } catch (error) {
      this.inFlight = null;
      this.attempts += 1;
      const err = error instanceof Error ? error : new Error("Persist failed");
      if (isFinal || step === "complete") {
        this.onUpdate(null, err, true);
      } else {
        // Quiet background failure — do not surface as tour content.
        this.onUpdate(null, null, false);
      }
      if (this.attempts >= this.maxAttempts) {
        this.pending = null;
        if (step === "complete") this.onUpdate(null, err, true);
        return;
      }
      this.pending = step;
      const delay = Math.min(8000, 400 * 2 ** (this.attempts - 1));
      this.timer = window.setTimeout(() => {
        this.timer = null;
        void this.drain(step === "complete");
      }, delay);
    }
  }
}
