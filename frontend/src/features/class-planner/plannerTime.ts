import { useSyncExternalStore } from "react";
import { PLANNER_TERM } from "./plannerData";
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
  return clock.currentWeekday === day && clock.isInstructionDay;
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
