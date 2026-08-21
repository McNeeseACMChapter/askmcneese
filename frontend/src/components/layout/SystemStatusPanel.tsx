import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CircleCheck,
  CircleX,
  HelpCircle,
  ShieldCheck,
  UserRound,
} from "lucide-react";
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
  const slots = Array.from({ length: Math.max(1, limit) }, (_, index) => index < used);
  const serviceTitle =
    online === null ? "Checking service" : online ? "AskMcNeese is ready" : "Service is unavailable";
  const serviceDetail =
    online === false
      ? "Your remaining allowance is unchanged until a request is accepted."
      : "A question counts only after the backend accepts it for research.";

  return (
    <RouteEnter>
      <main className="usagePage">
        <section className="usageHero" aria-labelledby="usage-title">
          <div className="usageHero__backdrop" aria-hidden="true">{remaining}</div>
          <div className="usageHero__content">
            <p className="usageKicker usageKicker--gold">Usage / Closed beta</p>
            <h1 id="usage-title">
              Your beta allowance.
              <em>Clear and local.</em>
            </h1>
            <p className="usageHero__lede">
              See what this browser has used, what remains, and whether the
              AskMcNeese service is ready before you ask.
            </p>
            <Link to="/ask" className="usageAction">
              Use AskMcNeese <ArrowRight aria-hidden="true" />
            </Link>
          </div>

          <aside className="usageAllowance" aria-label="Current closed-beta allowance">
            <header>
              <span><UserRound aria-hidden="true" /> Browser identity</span>
              <strong>{guestAlias ?? "Guest"}</strong>
            </header>
            <div className="usageAllowance__number">
              <span>{remaining}</span>
              <p>
                question{remaining === 1 ? "" : "s"} remaining
                <small>{used} of {limit} used</small>
              </p>
            </div>
            <div
              className="usageAllowance__meter"
              role="progressbar"
              aria-label={`${used} of ${limit} beta questions used`}
              aria-valuemin={0}
              aria-valuemax={limit}
              aria-valuenow={used}
            >
              {slots.map((slotUsed, index) => (
                <span key={index} className={slotUsed ? "is-used" : undefined} />
              ))}
            </div>
            <p className="usageAllowance__percent">{Math.round(percent)}% of this allowance used</p>
          </aside>
        </section>

        <section className="usageOverview" aria-labelledby="usage-overview-title">
          <header className="usageOverview__header">
            <div>
              <p className="usageKicker">Current state</p>
              <h2 id="usage-overview-title">What this browser can use.</h2>
            </div>
            <p>
              The allowance belongs to this guest identity—not to a conversation.
              Its state returns with this browser.
            </p>
          </header>

          <div className="usageFacts">
            <article className="usageFact usageFact--status" data-online={online === true ? "true" : online === false ? "false" : "checking"}>
              <div className="usageFact__icon">
                {online === null ? (
                  <HelpCircle aria-hidden="true" />
                ) : online ? (
                  <CircleCheck aria-hidden="true" />
                ) : (
                  <CircleX aria-hidden="true" />
                )}
              </div>
              <p className="usageKicker">Service</p>
              <h3>{serviceTitle}</h3>
              <p>{serviceDetail}</p>
            </article>

            <article className="usageFact">
              <div className="usageFact__icon"><ShieldCheck aria-hidden="true" /></div>
              <p className="usageKicker">Counting rule</p>
              <h3>Accepted questions count.</h3>
              <p>
                Drafts and failed submissions do not spend the allowance. An
                accepted research request uses one question.
              </p>
            </article>

            <article className="usageFact">
              <div className="usageFact__icon"><UserRound aria-hidden="true" /></div>
              <p className="usageKicker">Persistence</p>
              <h3>History and usage are separate.</h3>
              <p>
                Clearing conversation history does not reset the guest identity
                or restore used questions.
              </p>
            </article>
          </div>

          <footer className="usageBoundary">
            <span>Closed-beta boundary</span>
            <p>
              This allowance applies only to AskMcNeese&apos;s student-project beta.
              It does not affect McNeese accounts, registration, billing, or other university services.
            </p>
          </footer>
        </section>
      </main>
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
