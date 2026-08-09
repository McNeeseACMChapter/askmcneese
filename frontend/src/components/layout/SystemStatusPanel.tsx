import { useEffect, useState } from "react";
import { CircleCheck, CircleX, HelpCircle, UserRound } from "lucide-react";
import { useTour } from "../../features/onboarding";
import { RouteEnter } from "../motion/RouteEnter";
import { fetchHealth } from "../../lib/api";

export function SystemStatusPanel() {
  const [online, setOnline] = useState<boolean | null>(null);
  const { guestAlias, guestUsage } = useTour();

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal)
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
    return () => controller.abort();
  }, []);

  const used = guestUsage?.questionsUsed ?? 0;
  const limit = guestUsage?.questionLimit ?? 10;
  const remaining = guestUsage?.questionsRemaining ?? Math.max(0, limit - used);
  const percent = Math.min(100, Math.max(0, (used / Math.max(1, limit)) * 100));

  return (
    <RouteEnter>
      <Panel
        title="Usage"
        description="Your closed-beta allowance and service availability for this browser."
      >
        <section className="overflow-hidden rounded-2xl border border-border bg-surface">
          <div className="grid gap-6 p-5 sm:grid-cols-[1fr_auto] sm:items-end">
            <div>
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-secondary">
                <UserRound size={17} aria-hidden />
                <span>{guestAlias ?? "Guest"}</span>
              </div>
              <p className="font-editorial text-5xl font-semibold leading-none text-mcneese-blue">
                {remaining}
              </p>
              <p className="mt-2 text-sm text-text-secondary">
                question{remaining === 1 ? "" : "s"} remaining in this beta
              </p>
            </div>
            <p className="text-sm text-text-muted">{used} of {limit} used</p>
          </div>
          <div className="h-2 bg-surface-muted" aria-label={used + " of " + limit + " questions used"}>
            <div
              className="h-full bg-gradient-to-r from-mcneese-blue to-mcneese-gold transition-[width] duration-300"
              style={{ width: percent + "%" }}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-5">
          <div className="flex items-start gap-3">
            {online === null ? (
              <HelpCircle className="mt-0.5 text-text-muted" size={20} aria-hidden />
            ) : online ? (
              <CircleCheck className="mt-0.5 text-success" size={20} aria-hidden />
            ) : (
              <CircleX className="mt-0.5 text-error" size={20} aria-hidden />
            )}
            <div>
              <p className="font-semibold">
                {online === null ? "Checking service" : online ? "AskMcNeese is ready" : "Service is unavailable"}
              </p>
              <p className="mt-1 text-sm text-text-muted">
                {online
                  ? "A question is counted when the backend accepts it for research."
                  : "Your remaining allowance is unchanged until a request is accepted."}
              </p>
            </div>
          </div>
        </section>

        <p className="text-sm leading-6 text-text-muted">
          This guest identity and its remaining allowance return when you revisit from the same browser.
          Clearing conversation history does not reset the allowance.
        </p>
      </Panel>
    </RouteEnter>
  );
}

export function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <main className="w-full px-5 py-8 md:px-8 md:py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="font-editorial text-3xl font-semibold">{title}</h1>
        <p className="mt-1 text-text-secondary">{description}</p>
        <div className="mt-6 space-y-4">{children}</div>
      </div>
    </main>
  );
}
