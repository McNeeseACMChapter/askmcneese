import { formatSearchDates } from "./utils";
import type { DevelopmentChapter, ProjectUpdate, UpdateArea } from "./types";
import { DEVELOPMENT_CHAPTERS } from "./chapters";
import { assignedTicketNumbers, recordsFromCsv, toProjectUpdate } from "./parseTimeline";

/** Canonical PM timeline. Do not edit events here — change docs/pm/timeline.csv. */
import timelineCsv from "virtual:pm-timeline";

function assertCompleteAssignment(events: ProjectUpdate[]): void {
  const tickets = events.map((event) => event.ticketNo).sort((a, b) => a - b);
  const assigned = assignedTicketNumbers();
  const expected = Array.from({ length: tickets.length }, (_, i) => tickets[0] + i);

  if (tickets.join(",") !== assigned.join(",")) {
    throw new Error("Canonical timeline tickets and chapter tickets do not match");
  }
  if (tickets.join(",") !== expected.join(",")) {
    throw new Error("Canonical timeline tickets are missing or duplicated");
  }
}

export const projectUpdates: ProjectUpdate[] = recordsFromCsv(timelineCsv).map(toProjectUpdate);

assertCompleteAssignment(projectUpdates);

export const developmentChapters: DevelopmentChapter[] = DEVELOPMENT_CHAPTERS;

export const firstHistoricalEvent = projectUpdates.reduce((first, event) =>
  event.date < first.date ||
  (event.date === first.date && event.ticketNo < first.ticketNo)
    ? event
    : first,
);

export const latestHistoricalEvent = projectUpdates.reduce((latest, event) =>
  event.date > latest.date ||
  (event.date === latest.date && event.ticketNo > latest.ticketNo)
    ? event
    : latest,
);

/** Semantic freshness for the public record; never use file or deployment timestamps. */
export const recordFreshness = {
  date: latestHistoricalEvent.date,
  ticketNo: latestHistoricalEvent.ticketNo,
  title: latestHistoricalEvent.title,
};

export const developmentMetrics = [
  { value: String(projectUpdates.length), label: "Recorded project events" },
  { value: "16 / 16", label: "Sprint 1 backlog completed" },
  { value: "25", label: "Campus intelligence domain packs" },
  { value: "1,606", label: "Fall 2026 Class Planner sections" },
  { value: "13", label: "Transition developer guides" },
];

/** Current repository-backed stack, grouped for technical readers. */
export const projectTechnologyStack = [
  {
    label: "Frontend",
    technologies: ["React", "TypeScript", "Vite", "React Router", "Framer Motion", "Tailwind CSS"],
  },
  {
    label: "Backend & AI",
    technologies: ["Python", "FastAPI", "Uvicorn", "Anthropic Claude", "Server-Sent Events"],
  },
  {
    label: "Retrieval & crawling",
    technologies: ["ChromaDB", "RCCS", "Playwright", "Beautiful Soup", "PyPDF2"],
  },
  {
    label: "Data & delivery",
    technologies: ["PostgreSQL", "SQLAlchemy", "Alembic", "GitHub Actions", "Render"],
  },
  {
    label: "Verification",
    technologies: ["Vitest", "Testing Library", "Pytest", "TypeScript compiler"],
  },
];

export function eventsForChapter(chapterId: string): ProjectUpdate[] {
  return projectUpdates.filter((event) => event.chapterId === chapterId);
}

export function eventByTicket(ticketNo: number): ProjectUpdate | undefined {
  return projectUpdates.find((event) => event.ticketNo === ticketNo);
}

export function searchHaystack(event: ProjectUpdate, chapter?: DevelopmentChapter): string {
  const contributorText = event.contributors
    .map((contributor) => `${contributor.name} ${contributor.role ?? ""}`)
    .join(" ");
  return [
    String(event.ticketNo),
    event.date,
    formatSearchDates(event.date),
    event.title,
    contributorText,
    event.method,
    event.notes,
    event.commit,
    event.pullRequest,
    event.sprint,
    event.areas.join(" "),
    event.technologies.join(" "),
    chapter?.title,
    chapter?.id,
    chapter?.dateLabel,
  ]
    .filter(Boolean)
    .join(" ")
    .replace(/[_/.-]+/g, " ")
    .toLowerCase();
}

export function eventMatchesQuery(event: ProjectUpdate, query: string, chapter?: DevelopmentChapter): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;
  return searchHaystack(event, chapter).includes(needle);
}

export function eventMatchesArea(event: ProjectUpdate, area: "All" | UpdateArea): boolean {
  if (area === "All") return true;
  return event.areas.includes(area);
}
