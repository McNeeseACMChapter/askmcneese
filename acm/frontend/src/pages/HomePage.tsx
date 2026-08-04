import {
  ArrowRight,
  CalendarDays,
  CircleAlert,
  Clock3,
  FolderKanban,
  Gavel,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";
import { PageChrome } from "../components/layout/PageChrome";
import { ProgressBar } from "../components/viz/ProgressBar";
import { Sparkline } from "../components/viz/Sparkline";
import { StatusBadge, healthToTone } from "../components/ui/StatusBadge";
import { useFixtureState, usePulseQuery } from "../data/hooks";
import { routeManifest } from "../routes/manifest";
import { usePrototype } from "../state/PrototypeContext";

const route = routeManifest.find((r) => r.id === "home")!;

function formatMeetingWhen(start: string) {
  return new Date(start).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDueDate(value: string) {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function HomePage() {
  const { user, roleId } = usePrototype();
  const state = useFixtureState();
  const { data: pulse } = usePulseQuery();

  const attention = state.workItems
    .filter(
      (item) =>
        (item.ownerRole === roleId || item.ownerRole === "any") &&
        (item.bucket === "now" || item.bucket === "overdue"),
    )
    .sort((a, b) => Number(b.bucket === "overdue") - Number(a.bucket === "overdue"));

  const activeProjects = state.projects.filter((project) => !project.archived);
  const scheduledMeetings = [...state.meetings].sort((a, b) => a.start.localeCompare(b.start));
  const upcomingMeetings = scheduledMeetings.filter(
    (meeting) => new Date(meeting.start).getTime() >= Date.now(),
  );
  const agenda = (
    upcomingMeetings.length > 0 ? upcomingMeetings : [...scheduledMeetings].reverse()
  ).slice(0, 3);
  const nextMeeting = agenda[0];
  const decisions = state.decisions.slice(0, 3);
  const activityToday = pulse.activity7d.at(-1) ?? 0;

  return (
    <PageChrome route={route} title={`Welcome back, ${user.name.split(" ")[0]}`}>
      <section className="home-brief" aria-labelledby="home-brief-title">
        <div className="home-brief__lead">
          <p className="home-eyebrow">Chapter briefing · {user.roleLabel}</p>
          <h2 id="home-brief-title">
            {attention.length > 0
              ? `${attention.length} ${attention.length === 1 ? "item needs" : "items need"} your attention.`
              : "The immediate queue is clear."}
          </h2>
          <p>
            Start with decisions that can unblock people, then scan the portfolio for work
            that may slip.
          </p>
        </div>

        <dl className="home-brief__signals" aria-label="Chapter condition">
          <div>
            <dt>Open actions</dt>
            <dd>{pulse.attentionCount}</dd>
          </div>
          <div>
            <dt>Projects at risk</dt>
            <dd>{pulse.projectsAtRisk}</dd>
          </div>
          <div>
            <dt>Waiting approval</dt>
            <dd>{pulse.approvalsWaiting}</dd>
          </div>
        </dl>

        {nextMeeting ? (
          <Link to="/meetings" className="home-brief__meeting">
            <span className="home-brief__meeting-icon" aria-hidden>
              <CalendarDays size={19} strokeWidth={1.8} />
            </span>
            <span>
              <span className="home-brief__meeting-label">Next on the calendar</span>
              <strong>{nextMeeting.title}</strong>
              <small>{formatMeetingWhen(nextMeeting.start)} · {nextMeeting.location}</small>
            </span>
            <ArrowRight size={18} strokeWidth={1.8} aria-hidden />
          </Link>
        ) : null}
      </section>

      <div className="home-command-grid">
        <div className="home-workspace">
          <section className="home-workspace__section" aria-labelledby="priority-title">
            <div className="home-section-head">
              <div>
                <p className="home-eyebrow">Priority desk</p>
                <h2 id="priority-title">Needs your attention</h2>
                <p>Now and overdue work assigned to {user.roleLabel}.</p>
              </div>
              <Link to="/my-work" className="home-text-link">
                See all work <ArrowRight size={16} aria-hidden />
              </Link>
            </div>

            {attention.length === 0 ? (
              <div className="home-empty">
                <span aria-hidden>✓</span>
                <p>Nothing needs a decision right now.</p>
              </div>
            ) : (
              <ol className="home-priority-list">
                {attention.map((item, index) => (
                  <li key={item.id} className="home-priority-row">
                    <span className="home-priority-row__index" aria-hidden>
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div className="home-priority-row__body">
                      <div className="home-priority-row__title">
                        <Link to={item.href}>{item.title}</Link>
                        <StatusBadge label={item.status} tone={item.statusTone} />
                      </div>
                      <p>{item.reason}</p>
                      <span>{item.parentLabel} · Due {item.deadline}</span>
                    </div>
                    <Link
                      to={item.href}
                      className="home-row-action"
                      aria-label={`${item.actionLabel}: ${item.title}`}
                    >
                      <span>{item.actionLabel}</span>
                      <ArrowRight size={17} strokeWidth={1.8} aria-hidden />
                    </Link>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section className="home-workspace__section home-portfolio" aria-labelledby="portfolio-title">
            <div className="home-section-head">
              <div>
                <p className="home-eyebrow">Active portfolio</p>
                <h2 id="portfolio-title">Where delivery stands</h2>
                <p>Health, ownership, progress, and the next committed milestone.</p>
              </div>
              <Link to="/projects" className="home-text-link">
                Open projects <ArrowRight size={16} aria-hidden />
              </Link>
            </div>

            <div className="home-portfolio-table" role="table" aria-label="Active project portfolio">
              <div className="home-portfolio-row home-portfolio-row--header" role="row">
                <span role="columnheader">Project</span>
                <span role="columnheader">Health</span>
                <span role="columnheader">Progress</span>
                <span role="columnheader">Next milestone</span>
              </div>
              {activeProjects.map((project) => {
                const health = healthToTone(project.health);
                return (
                  <div className="home-portfolio-row" role="row" key={project.id}>
                    <div className="home-portfolio-row__project" role="cell">
                      <span className="home-avatar" aria-hidden>{project.ownerInitials}</span>
                      <span>
                        <Link to={`/projects/${project.id}`}>{project.name}</Link>
                        <small>{project.owner} · Updated {project.updated}</small>
                      </span>
                    </div>
                    <div role="cell" data-label="Health">
                      <StatusBadge label={health.label} tone={health.tone} />
                    </div>
                    <div className="home-portfolio-row__progress" role="cell" data-label="Progress">
                      <ProgressBar value={project.progressPercent} label={`${project.name} progress`} />
                    </div>
                    <div className="home-portfolio-row__milestone" role="cell" data-label="Next milestone">
                      <strong>{project.nextMilestone}</strong>
                      <small>Due {formatDueDate(project.dueDate)}</small>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        <aside className="home-pulse" aria-label="Chapter pulse">
          <section className="home-pulse__section" aria-labelledby="activity-title">
            <div className="home-pulse__heading">
              <span className="home-pulse__icon" aria-hidden><TrendingUp size={18} /></span>
              <div>
                <p className="home-eyebrow">Seven-day pulse</p>
                <h2 id="activity-title">{activityToday} actions today</h2>
              </div>
            </div>
            <div className="home-activity-chart">
              <Sparkline
                values={pulse.activity7d}
                label="Chapter activity, last 7 days"
                width={236}
                height={58}
                categories={["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].slice(0, pulse.activity7d.length)}
              />
            </div>
            <p className="home-pulse__note">A steady week of recorded chapter activity.</p>
          </section>

          <section className="home-pulse__section" aria-labelledby="agenda-title">
            <div className="home-pulse__heading">
              <span className="home-pulse__icon" aria-hidden><Clock3 size={18} /></span>
              <div>
                <p className="home-eyebrow">Calendar</p>
                <h2 id="agenda-title">What’s next</h2>
              </div>
            </div>
            <ol className="home-agenda">
              {agenda.map((meeting, index) => (
                <li key={meeting.id}>
                  <span className="home-agenda__rail" aria-hidden>
                    <span>{index + 1}</span>
                  </span>
                  <div>
                    <strong>{meeting.title}</strong>
                    <p>{formatMeetingWhen(meeting.start)}</p>
                    <small>{meeting.location}</small>
                  </div>
                </li>
              ))}
            </ol>
            <Link to="/meetings" className="home-text-link">
              View calendar <ArrowRight size={16} aria-hidden />
            </Link>
          </section>

          <section className="home-pulse__section" aria-labelledby="decisions-title">
            <div className="home-pulse__heading">
              <span className="home-pulse__icon" aria-hidden><Gavel size={18} /></span>
              <div>
                <p className="home-eyebrow">Institutional memory</p>
                <h2 id="decisions-title">Recent decisions</h2>
              </div>
            </div>
            <ul className="home-decision-list">
              {decisions.map((decision) => (
                <li key={decision.id}>
                  <span aria-hidden><CircleAlert size={15} /></span>
                  <div>
                    <strong>{decision.title}</strong>
                    <small>{decision.at} · {decision.status}</small>
                  </div>
                </li>
              ))}
            </ul>
            <Link to="/governance" className="home-text-link">
              Open governance <ArrowRight size={16} aria-hidden />
            </Link>
          </section>

          <Link to="/projects" className="home-pulse__footer">
            <FolderKanban size={18} aria-hidden />
            <span>
              <strong>{activeProjects.length} active projects</strong>
              <small>Review the complete portfolio</small>
            </span>
            <ArrowRight size={17} aria-hidden />
          </Link>
        </aside>
      </div>
    </PageChrome>
  );
}