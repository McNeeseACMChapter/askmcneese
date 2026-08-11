import {
  BookOpenCheck,
  CalendarCheck2,
  DatabaseZap,
  History,
  MessageSquareText,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react";
import { RouteEnter } from "../components/motion/RouteEnter";

const releaseUpdates = [
  {
    date: "2026-08-11",
    label: "August 11",
    title: "A guest session that remembers this browser",
    detail:
      "Your anonymous guest identity, walkthrough progress, and beta allowance now return with you on this browser. AskMcNeese does not fingerprint your device.",
    icon: UserRoundCheck,
  },
  {
    date: "2026-08-10",
    label: "August 10",
    title: "Class Search moved to validated McNeese data",
    detail:
      "Course search and schedule planning now read a published dataset. A failed sync keeps the last good copy, and production never replaces it with demo classes.",
    icon: DatabaseZap,
  },
  {
    date: "2026-08-09",
    label: "August 9",
    title: "Phone planning and conversation history feel dependable",
    detail:
      "Sections load when needed, schedule gaps calculate correctly, and History supports opening, renaming, swiping, and confirmed deletion.",
    icon: History,
  },
  {
    date: "2026-08-08",
    label: "August 8",
    title: "The public beta became one connected experience",
    detail:
      "Source-grounded Ask, the 14-step guest walkthrough, Class Planner, feedback, and the public information pages now share one responsive product shell.",
    icon: ShieldCheck,
  },
] as const;

const availableNow = [
  { label: "Ask McNeese questions with visible sources", icon: MessageSquareText },
  { label: "Search classes and build a local weekly plan", icon: CalendarCheck2 },
  { label: "Return to conversations saved in this browser", icon: History },
] as const;

export function UpdatesPage() {
  return (
    <RouteEnter>
      <main className="updatesPage">
        <div className="updatesPage__mesh" aria-hidden="true" />
        <div className="updatesPage__inner">
          <header className="updatesPage__hero">
            <div>
              <h1>Updates that make AskMcNeese more dependable.</h1>
              <p>
                The latest work is focused on clearer answers, real class data, and a guest
                experience that works the same way when you return.
              </p>
            </div>
            <div className="updatesPage__release" aria-label="Current release">
              <ShieldCheck size={24} strokeWidth={1.8} aria-hidden="true" />
              <div>
                <strong>Public beta</strong>
                <span>Current build · August 2026</span>
              </div>
            </div>
          </header>

          <section className="updatesPage__ledger" aria-labelledby="updates-ledger-title">
            <header className="updatesPage__sectionHeader">
              <h2 id="updates-ledger-title">What changed</h2>
              <p>Four meaningful improvements, written in plain language.</p>
            </header>

            <ol className="updatesPage__timeline">
              {releaseUpdates.map(({ date, label, title, detail, icon: Icon }) => (
                <li key={title}>
                  <time dateTime={date}>{label}</time>
                  <span className="updatesPage__timelineIcon" aria-hidden="true">
                    <Icon size={21} strokeWidth={1.8} />
                  </span>
                  <div>
                    <h3>{title}</h3>
                    <p>{detail}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className="updatesPage__nowNext" aria-label="Current and planned capabilities">
            <div className="updatesPage__now">
              <h2>Available now</h2>
              <ul>
                {availableNow.map(({ label, icon: Icon }) => (
                  <li key={label}>
                    <Icon size={20} strokeWidth={1.8} aria-hidden="true" />
                    <span>{label}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="updatesPage__next">
              <BookOpenCheck size={28} strokeWidth={1.7} aria-hidden="true" />
              <div>
                <h2>Next direction</h2>
                <p>
                  Broader answer coverage comes first. Canvas-connected course context is a
                  later direction and will require clear consent, privacy review, and secure
                  McNeese access before it becomes available.
                </p>
              </div>
            </div>
          </section>

          <p className="updatesPage__boundary">
            AskMcNeese is a beta guide. Registration, grades, billing, and other personal
            records remain in McNeese&apos;s authenticated systems.
          </p>
        </div>
      </main>
    </RouteEnter>
  );
}
