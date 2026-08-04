import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { CompactMetric } from "../components/viz/CompactMetric";
import { ProgressBar } from "../components/viz/ProgressBar";
import { ProgressRing } from "../components/viz/ProgressRing";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";

const route = routeManifest.find((r) => r.id === "events")!;

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function EventsPage() {
  const state = useFixtureState();
  const events = [...state.events].sort((a, b) => a.start.localeCompare(b.start));
  const avgReadiness = Math.round(
    events.reduce((sum, e) => sum + e.readiness, 0) / Math.max(events.length, 1),
  );

  return (
    <PageChrome route={route} title="Events">
      <div className="acm-metric-strip">
        <CompactMetric label="Upcoming events" value={events.length} />
        <CompactMetric label="Avg. readiness" value={`${avgReadiness}%`} />
        <CompactMetric
          label="Venue confirmed"
          value={events.filter((e) => e.venueReady).length}
          hint={`of ${events.length}`}
        />
        <CompactMetric
          label="Budget cleared"
          value={events.filter((e) => e.budgetOk).length}
          hint={`of ${events.length}`}
        />
      </div>

      <div className="space-y-4">
        {events.map((event) => (
          <Surface key={event.id} level="content" className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-lg">{event.title}</h2>
                <p className="text-sm text-text-secondary">
                  {formatDate(event.start)} – {formatDate(event.end)}
                </p>
              </div>
              <ProgressRing value={event.readiness} label="Readiness" />
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  Registration
                </p>
                <div className="mt-1">
                  <ProgressBar value={event.registrationPercent} label="Registration" />
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                  Volunteer coverage
                </p>
                <div className="mt-1">
                  <ProgressBar value={event.volunteerCoverage} label="Volunteer coverage" />
                </div>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <StatusBadge
                label={event.venueReady ? "Venue confirmed" : "Venue pending"}
                tone={event.venueReady ? "success" : "warning"}
              />
              <StatusBadge
                label={event.promotionReady ? "Promotion ready" : "Promotion pending"}
                tone={event.promotionReady ? "success" : "warning"}
              />
              <StatusBadge
                label={event.budgetOk ? "Budget cleared" : "Budget blocked"}
                tone={event.budgetOk ? "success" : "danger"}
              />
            </div>
          </Surface>
        ))}
      </div>
    </PageChrome>
  );
}
