import { useSyncExternalStore } from "react";
import { PLANNER_TERM } from "./plannerCalendar";
import type { Meeting, MeetingDay } from "./plannerTypes";

export type MeetingTemporalState = "inactive" | "upcoming" | "current" | "completed";

export interface PlannerClockSnapshot {
  now: Date;
  currentDate: string;
  currentMinutes: number;
  currentWeekday: MeetingDay | null;
  isTermActive: boolean;
  isInstructionDay: boolean;
}

export interface MeetingTemporalInfo {
  state: MeetingTemporalState;
  progress: number;
  minutesUntilStart: number | null;
  minutesRemaining: number | null;
}

export interface PlannerWeekDate {
  day: MeetingDay;
  date: string;
  dayNumber: number;
  shortLabel: string;
  longLabel: string;
}

const plannerWeekdays: MeetingDay[] = ["M", "T", "W", "R", "F"];

const weekdayMap: Record<string, MeetingDay> = {
  Mon: "M",
  Tue: "T",
  Wed: "W",
  Thu: "R",
  Fri: "F",
  Sat: "S",
  Sun: "U",
};

const clockFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: PLANNER_TERM.timezone,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  weekday: "short",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

const timeLabelFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: PLANNER_TERM.timezone,
  hour: "numeric",
  minute: "2-digit",
});

function dateParts(now: Date) {
  return Object.fromEntries(
    clockFormatter.formatToParts(now).map((part) => [part.type, part.value]),
  );
}

export function getPlannerClockSnapshot(now = new Date(Date.now())): PlannerClockSnapshot {
  const parts = dateParts(now);
  const currentDate = `${parts.year}-${parts.month}-${parts.day}`;
  const currentWeekday = weekdayMap[parts.weekday] ?? null;
  const isTermActive = currentDate >= PLANNER_TERM.classStartDate
    && currentDate <= PLANNER_TERM.classEndDate;
  const isInstructionDay = isTermActive
    && !PLANNER_TERM.noClassDates.includes(currentDate as typeof PLANNER_TERM.noClassDates[number]);

  return {
    now,
    currentDate,
    currentMinutes: Number(parts.hour) * 60 + Number(parts.minute),
    currentWeekday,
    isTermActive,
    isInstructionDay,
  };
}

export function isPlannerToday(day: MeetingDay, clock: PlannerClockSnapshot): boolean {
  return clock.currentWeekday === day;
}

export function getPlannerWeekDates(currentDate: string, weekOffset = 0): PlannerWeekDate[] {
  const anchor = new Date(`${currentDate}T12:00:00Z`);
  const mondayOffset = (anchor.getUTCDay() + 6) % 7;
  const monday = new Date(anchor);
  monday.setUTCDate(anchor.getUTCDate() - mondayOffset + weekOffset * 7);

  return plannerWeekdays.map((day, index) => {
    const date = new Date(monday);
    date.setUTCDate(monday.getUTCDate() + index);
    const isoDate = date.toISOString().slice(0, 10);
    return {
      day,
      date: isoDate,
      dayNumber: date.getUTCDate(),
      shortLabel: new Intl.DateTimeFormat("en-US", {
        timeZone: "UTC",
        month: "short",
        day: "numeric",
      }).format(date),
      longLabel: new Intl.DateTimeFormat("en-US", {
        timeZone: "UTC",
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      }).format(date),
    };
  });
}

export function formatPlannerWeekRange(days: PlannerWeekDate[]): string {
  const first = days[0];
  const last = days[days.length - 1];
  if (!first || !last) return "";
  const firstDate = new Date(`${first.date}T12:00:00Z`);
  const lastDate = new Date(`${last.date}T12:00:00Z`);
  const firstYear = firstDate.getUTCFullYear();
  const lastYear = lastDate.getUTCFullYear();
  const sameYear = firstYear === lastYear;
  const sameMonth = sameYear && firstDate.getUTCMonth() === lastDate.getUTCMonth();
  const monthDay = new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
  });
  if (sameMonth) {
    const month = new Intl.DateTimeFormat("en-US", {
      timeZone: "UTC",
      month: "short",
    }).format(firstDate);
    return `${month} ${first.dayNumber}–${last.dayNumber}, ${firstYear}`;
  }
  if (sameYear) return `${monthDay.format(firstDate)}–${monthDay.format(lastDate)}, ${firstYear}`;
  return `${first.longLabel.replace(/^\w+, /, "")}–${last.longLabel.replace(/^\w+, /, "")}`;
}

export function meetingOccursOnPlannerDate(meeting: Meeting, date: string): boolean {
  const startDate = meeting.startDate ?? PLANNER_TERM.classStartDate;
  const endDate = meeting.endDate ?? PLANNER_TERM.classEndDate;
  return date >= startDate
    && date <= endDate
    && !PLANNER_TERM.noClassDates.includes(date as typeof PLANNER_TERM.noClassDates[number]);
}

export function getMeetingTemporalInfo(
  meeting: Meeting,
  clock: PlannerClockSnapshot,
): MeetingTemporalInfo {
  if (
    !clock.isInstructionDay
    || !clock.currentWeekday
    || !meeting.days.includes(clock.currentWeekday)
    || !meeting.startTime
    || !meeting.endTime
    || (meeting.startDate && clock.currentDate < meeting.startDate)
    || (meeting.endDate && clock.currentDate > meeting.endDate)
  ) {
    return { state: "inactive", progress: 0, minutesUntilStart: null, minutesRemaining: null };
  }

  const start = minutesFromClockTime(meeting.startTime);
  const end = minutesFromClockTime(meeting.endTime);
  if (clock.currentMinutes < start) {
    return {
      state: "upcoming",
      progress: 0,
      minutesUntilStart: start - clock.currentMinutes,
      minutesRemaining: null,
    };
  }
  if (clock.currentMinutes >= end) {
    return {
      state: "completed",
      progress: 1,
      minutesUntilStart: null,
      minutesRemaining: 0,
    };
  }

  return {
    state: "current",
    progress: Math.max(0, Math.min(1, (clock.currentMinutes - start) / Math.max(1, end - start))),
    minutesUntilStart: 0,
    minutesRemaining: end - clock.currentMinutes,
  };
}

export function formatPlannerNow(clock: PlannerClockSnapshot): string {
  return timeLabelFormatter.format(clock.now);
}

function minutesFromClockTime(time: string): number {
  const [hours, minutes] = time.split(":").map(Number);
  return hours * 60 + minutes;
}

let snapshot = getPlannerClockSnapshot();
const listeners = new Set<() => void>();
let minuteTimer: number | null = null;

function refreshClock() {
  snapshot = getPlannerClockSnapshot();
  listeners.forEach((listener) => listener());
}

function scheduleMinuteBoundary() {
  if (typeof window === "undefined" || !listeners.size) return;
  if (minuteTimer !== null) window.clearTimeout(minuteTimer);
  const delay = 60_000 - (Date.now() % 60_000) + 25;
  minuteTimer = window.setTimeout(() => {
    refreshClock();
    scheduleMinuteBoundary();
  }, delay);
}

function reconcileVisibleClock() {
  if (typeof document === "undefined" || document.visibilityState === "visible") {
    refreshClock();
    scheduleMinuteBoundary();
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (listeners.size === 1 && typeof window !== "undefined") {
    refreshClock();
    scheduleMinuteBoundary();
    document.addEventListener("visibilitychange", reconcileVisibleClock);
    window.addEventListener("focus", reconcileVisibleClock);
  }
  return () => {
    listeners.delete(listener);
    if (!listeners.size && typeof window !== "undefined") {
      if (minuteTimer !== null) window.clearTimeout(minuteTimer);
      minuteTimer = null;
      document.removeEventListener("visibilitychange", reconcileVisibleClock);
      window.removeEventListener("focus", reconcileVisibleClock);
    }
  };
}

function getSnapshot() {
  return snapshot;
}

export function usePlannerNow(): PlannerClockSnapshot {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
