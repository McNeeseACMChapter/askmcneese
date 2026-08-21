import { useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import type { DevelopmentChapter, ProjectUpdate } from "./types";
import { formatExactDate } from "./utils";

const DAY_MS = 86_400_000;
const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

export interface CalendarCell {
  date: string;
  weekIndex: number;
  weekdayIndex: number;
  inRange: boolean;
  events: ProjectUpdate[];
}

export interface CalendarMonth {
  label: string;
  weekIndex: number;
}

export interface ContributionCalendarModel {
  firstDate: string;
  lastDate: string;
  weekCount: number;
  cells: CalendarCell[];
  months: CalendarMonth[];
}

interface EvolutionFieldProps {
  chapters: DevelopmentChapter[];
  events: ProjectUpdate[];
  activeChapterId: string | null;
  matchingTicketNos: Set<number>;
  filtersActive?: boolean;
  onOpenTicket?: (ticketNo: number) => void;
}

function timestampForIso(iso: string): number {
  const match = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) throw new Error(`Invalid calendar date: ${iso}`);
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const timestamp = Date.UTC(year, month - 1, day);
  const parsed = new Date(timestamp);
  if (
    parsed.getUTCFullYear() !== year ||
    parsed.getUTCMonth() !== month - 1 ||
    parsed.getUTCDate() !== day
  ) {
    throw new Error(`Invalid calendar date: ${iso}`);
  }
  return timestamp;
}

function isoForTimestamp(timestamp: number): string {
  return new Date(timestamp).toISOString().slice(0, 10);
}

export function contributionLevel(eventCount: number): 0 | 1 | 2 | 3 | 4 {
  if (eventCount === 0) return 0;
  if (eventCount === 1) return 1;
  if (eventCount <= 3) return 2;
  if (eventCount <= 7) return 3;
  return 4;
}

export function buildContributionCalendar(events: ProjectUpdate[]): ContributionCalendarModel {
  if (events.length === 0) {
    throw new Error("The contribution calendar requires at least one project event");
  }

  const sorted = [...events].sort(
    (left, right) => left.date.localeCompare(right.date) || left.ticketNo - right.ticketNo,
  );
  const firstDate = sorted[0].date;
  const lastDate = sorted[sorted.length - 1].date;
  const firstTimestamp = timestampForIso(firstDate);
  const lastTimestamp = timestampForIso(lastDate);
  const paddedStart = firstTimestamp - new Date(firstTimestamp).getUTCDay() * DAY_MS;
  const paddedEnd = lastTimestamp + (6 - new Date(lastTimestamp).getUTCDay()) * DAY_MS;
  const eventMap = new Map<string, ProjectUpdate[]>();

  for (const event of sorted) {
    timestampForIso(event.date);
    const dayEvents = eventMap.get(event.date) ?? [];
    dayEvents.push(event);
    eventMap.set(event.date, dayEvents);
  }

  const cells: CalendarCell[] = [];
  const months: CalendarMonth[] = [];
  let previousMonth = -1;

  for (let timestamp = paddedStart, offset = 0; timestamp <= paddedEnd; timestamp += DAY_MS, offset += 1) {
    const date = isoForTimestamp(timestamp);
    const weekIndex = Math.floor(offset / 7);
    const weekdayIndex = offset % 7;
    const inRange = timestamp >= firstTimestamp && timestamp <= lastTimestamp;
    cells.push({
      date,
      weekIndex,
      weekdayIndex,
      inRange,
      events: inRange ? eventMap.get(date) ?? [] : [],
    });

    const month = new Date(timestamp).getUTCMonth();
    if (inRange && month !== previousMonth) {
      months.push({ label: MONTH_LABELS[month], weekIndex });
      previousMonth = month;
    }
  }

  return {
    firstDate,
    lastDate,
    weekCount: Math.ceil(cells.length / 7),
    cells,
    months: months.filter(
      (month, index) =>
        index === months.length - 1 ||
        months[index + 1].weekIndex - month.weekIndex >= 2,
    ),
  };
}

function accessibleDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(timestampForIso(iso)));
}

export function EvolutionField({
  chapters,
  events,
  activeChapterId,
  matchingTicketNos,
  filtersActive = false,
  onOpenTicket,
}: EvolutionFieldProps) {
  const calendar = useMemo(() => buildContributionCalendar(events), [events]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const chapterById = useMemo(
    () => new Map(chapters.map((chapter) => [chapter.id, chapter])),
    [chapters],
  );
  const dateCells = calendar.cells.filter((cell) => cell.inRange);
  const selectedCell = selectedDate
    ? calendar.cells.find((cell) => cell.date === selectedDate)
    : undefined;
  const style = { "--updates-calendar-weeks": calendar.weekCount } as CSSProperties;

  function focusDate(currentDate: string, dayDelta: number, targetBoundary?: "start" | "end") {
    let targetTimestamp = timestampForIso(currentDate) + dayDelta * DAY_MS;
    if (targetBoundary === "start") targetTimestamp = timestampForIso(calendar.firstDate);
    if (targetBoundary === "end") targetTimestamp = timestampForIso(calendar.lastDate);
    targetTimestamp = Math.max(
      timestampForIso(calendar.firstDate),
      Math.min(timestampForIso(calendar.lastDate), targetTimestamp),
    );
    const target = document.querySelector<HTMLButtonElement>(
      `.updatesCalendar__day[data-date="${isoForTimestamp(targetTimestamp)}"]`,
    );
    target?.focus();
    target?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, cell: CalendarCell) {
    let handled = true;
    if (event.key === "ArrowLeft") focusDate(cell.date, -7);
    else if (event.key === "ArrowRight") focusDate(cell.date, 7);
    else if (event.key === "ArrowUp") focusDate(cell.date, -1);
    else if (event.key === "ArrowDown") focusDate(cell.date, 1);
    else if (event.key === "Home" && event.ctrlKey) focusDate(cell.date, 0, "start");
    else if (event.key === "End" && event.ctrlKey) focusDate(cell.date, 0, "end");
    else if (event.key === "Home") focusDate(cell.date, -cell.weekdayIndex);
    else if (event.key === "End") focusDate(cell.date, 6 - cell.weekdayIndex);
    else if (event.key === "Enter" || event.key === " ") setSelectedDate(cell.date);
    else handled = false;
    if (handled) event.preventDefault();
  }

  return (
    <figure className="updatesEvolution">
      <div className="updatesCalendar__scroll" tabIndex={0} aria-label="Scrollable development contribution calendar">
        <div className="updatesCalendar" style={style}>
          <div className="updatesCalendar__months" aria-hidden="true">
            {calendar.months.map((month) => (
              <span key={`${month.label}-${month.weekIndex}`} style={{ gridColumn: month.weekIndex + 1 }}>
                {month.label}
              </span>
            ))}
          </div>
          <div className="updatesCalendar__body">
            <div className="updatesCalendar__weekdays" aria-hidden="true">
              {WEEKDAY_LABELS.map((label, index) => <span key={index}>{label}</span>)}
            </div>
            <div
              className="updatesCalendar__grid"
              role="grid"
              aria-label={`${calendar.weekCount}-week project contribution calendar`}
            >
              {calendar.cells.map((cell) => {
                if (!cell.inRange) {
                  return (
                    <span
                      key={cell.date}
                      className="updatesCalendar__placeholder"
                      aria-hidden="true"
                      style={{ gridColumn: cell.weekIndex + 1, gridRow: cell.weekdayIndex + 1 }}
                    />
                  );
                }

                const matchedEvents = cell.events.filter((item) => matchingTicketNos.has(item.ticketNo));
                const chapterNames = [...new Set(cell.events.map((item) => chapterById.get(item.chapterId)?.title))]
                  .filter(Boolean)
                  .join(", ");
                const eventLabel = cell.events.length === 1 ? "event" : "events";
                const matchLabel = filtersActive
                  ? `; ${matchedEvents.length} match${matchedEvents.length === 1 ? "es" : ""} the current filters`
                  : "";
                const chapterLabel = chapterNames ? `; ${chapterNames}` : "";
                const hasTurningPoint = cell.events.some((item) => item.turningPoint);
                const hasActiveChapter = cell.events.some((item) => item.chapterId === activeChapterId);
                const selected = selectedDate === cell.date;
                const classes = [
                  "updatesCalendar__day",
                  hasTurningPoint ? "has-turning-point" : "",
                  hasActiveChapter ? "has-active-chapter" : "",
                  filtersActive && cell.events.length > 0 && matchedEvents.length === 0 ? "has-no-matches" : "",
                ].filter(Boolean).join(" ");

                return (
                  <button
                    key={cell.date}
                    type="button"
                    role="gridcell"
                    className={classes}
                    data-date={cell.date}
                    data-level={contributionLevel(cell.events.length)}
                    style={{ gridColumn: cell.weekIndex + 1, gridRow: cell.weekdayIndex + 1 }}
                    tabIndex={cell.date === calendar.lastDate ? 0 : -1}
                    aria-label={`${accessibleDate(cell.date)} — ${cell.events.length} recorded ${eventLabel}${matchLabel}${chapterLabel}`}
                    aria-selected={selected}
                    aria-expanded={selected}
                    aria-controls={selected ? "updates-calendar-detail" : undefined}
                    title={`${formatExactDate(cell.date)} · ${cell.events.length} ${eventLabel}`}
                    onClick={() => setSelectedDate(selected ? null : cell.date)}
                    onKeyDown={(event) => handleKeyDown(event, cell)}
                  >
                    <span aria-hidden="true" />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="updatesCalendar__footer">
        <figcaption>
          {events.length} verified events across {dateCells.filter((cell) => cell.events.length > 0).length} active days.
          Select a day to inspect its record.
        </figcaption>
        <div className="updatesCalendar__legend" aria-label="Contribution intensity from fewer to more events">
          <span>Less</span>
          {[0, 1, 2, 3, 4].map((level) => <i key={level} data-level={level} />)}
          <span>More</span>
        </div>
      </div>

      {selectedCell && (
        <div id="updates-calendar-detail" className="updatesCalendar__detail" aria-live="polite">
          <header>
            <div>
              <span className="updatesKicker">Selected day</span>
              <h3>{accessibleDate(selectedCell.date)}</h3>
            </div>
            <button type="button" onClick={() => setSelectedDate(null)}>Close</button>
          </header>
          {selectedCell.events.length === 0 ? (
            <p>No recorded development events on this date.</p>
          ) : (
            <ul>
              {selectedCell.events.map((event) => {
                const matches = matchingTicketNos.has(event.ticketNo);
                return (
                  <li key={event.ticketNo} data-matches={matches ? "true" : "false"}>
                    <a
                      href={`#ticket-${event.ticketNo}`}
                      onClick={() => onOpenTicket?.(event.ticketNo)}
                    >
                      <span>Ticket {event.ticketNo}</span>
                      {event.title}
                    </a>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </figure>
  );
}
