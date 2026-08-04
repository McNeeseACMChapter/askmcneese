import { useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import listPlugin from "@fullcalendar/list";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { ProgressBar } from "../components/viz/ProgressBar";
import { Sparkline } from "../components/viz/Sparkline";
import { LifecycleStepper } from "../components/viz/LifecycleStepper";
import { CompactMetric } from "../components/viz/CompactMetric";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { MeetingLifecycle } from "../data/types";

const route = routeManifest.find((r) => r.id === "meetings")!;

const lifecycleOrder: MeetingLifecycle[] = [
  "agenda_draft",
  "published",
  "in_progress",
  "minutes_draft",
  "under_review",
  "approved",
];

const lifecycleLabels: Record<MeetingLifecycle, string> = {
  agenda_draft: "Agenda draft",
  published: "Published",
  in_progress: "In progress",
  minutes_draft: "Minutes draft",
  under_review: "Under review",
  approved: "Approved",
};

function formatWhen(start: string, end: string) {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const day = startDate.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const startTime = startDate.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  const endTime = endDate.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${day} · ${startTime}–${endTime}`;
}

export function MeetingsPage() {
  const state = useFixtureState();
  const meetings = [...state.meetings].sort((a, b) => a.start.localeCompare(b.start));
  const quorumReadyCount = meetings.filter((m) => m.quorumReady).length;
  const avgAgenda = Math.round(
    meetings.reduce((sum, m) => sum + m.agendaCompletion, 0) / Math.max(meetings.length, 1),
  );
  const calendarEvents = useMemo(
    () =>
      meetings.map((m) => ({
        id: m.id,
        title: m.title,
        start: m.start,
        end: m.end,
        editable: false,
      })),
    [meetings],
  );

  return (
    <PageChrome route={route} title="Meetings">
      <div className="acm-metric-strip">
        <CompactMetric label="Scheduled" value={meetings.length} hint="Fixture calendar" />
        <CompactMetric label="Quorum ready" value={`${quorumReadyCount}/${meetings.length}`} />
        <CompactMetric label="Avg. agenda completion" value={`${avgAgenda}%`} />
        <CompactMetric
          label="Next up"
          value={meetings[0]?.title ?? "—"}
          hint={meetings[0] ? formatWhen(meetings[0].start, meetings[0].end) : undefined}
        />
      </div>

      <Surface level="content" className="p-4">
        <h2 className="text-lg">Chapter calendar</h2>
        <p className="mt-1 mb-3 text-sm text-text-secondary">
          Month and agenda views. Drag edits are disabled until a confirmed mutation path exists.
        </p>
        <div className="acm-calendar" aria-label="Meetings calendar">
          <FullCalendar
            plugins={[dayGridPlugin, listPlugin]}
            initialView="dayGridMonth"
            headerToolbar={{
              left: "prev,next today",
              center: "title",
              right: "dayGridMonth,listWeek",
            }}
            height="auto"
            editable={false}
            events={calendarEvents}
          />
        </div>
      </Surface>

      <div className="space-y-4">
        {meetings.map((meeting) => {
          const idx = lifecycleOrder.indexOf(meeting.lifecycle);
          const steps = lifecycleOrder.map((stage, i) => ({
            id: stage,
            label: lifecycleLabels[stage],
            done: i < idx,
            current: i === idx,
          }));
          return (
            <Surface key={meeting.id} level="content" className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg">{meeting.title}</h2>
                  <p className="text-sm text-text-secondary">
                    {formatWhen(meeting.start, meeting.end)} · {meeting.location}
                  </p>
                </div>
                <StatusBadge
                  label={meeting.quorumReady ? "Quorum ready" : "Quorum at risk"}
                  tone={meeting.quorumReady ? "success" : "warning"}
                />
              </div>
              <div className="mt-4">
                <LifecycleStepper steps={steps} label={`${meeting.title} lifecycle`} />
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-6">
                <div className="min-w-[200px] flex-1">
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Agenda completion
                  </p>
                  <div className="mt-1">
                    <ProgressBar value={meeting.agendaCompletion} label="Agenda completion" />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Attendance trend
                  </p>
                  <div className="mt-1">
                    <Sparkline values={meeting.attendanceTrend} label={`${meeting.title} attendance`} />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Minutes
                  </p>
                  <p className="mt-1 text-sm font-semibold text-text-primary">
                    {meeting.minutesStatus}
                  </p>
                </div>
              </div>
            </Surface>
          );
        })}
      </div>
    </PageChrome>
  );
}
