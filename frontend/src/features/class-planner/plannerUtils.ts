import type { Course, Meeting, MeetingDay, PlannerFilters, ScheduleConflict, Section } from "./plannerTypes";

export const DAY_LABELS: Record<MeetingDay, string> = {
  M: "Monday", T: "Tuesday", W: "Wednesday", R: "Thursday",
  F: "Friday", S: "Saturday", U: "Sunday",
};
export const WEEKDAYS: MeetingDay[] = ["M", "T", "W", "R", "F"];

export interface VisibleScheduleRange {
  start: number;
  end: number;
}

export function minutesFromTime(value: string): number {
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + minutes;
}

export function formatTime(value: string | null): string {
  if (!value) return "TBA";
  const [rawHour, minutes] = value.split(":").map(Number);
  const period = rawHour >= 12 ? "PM" : "AM";
  const hour = rawHour % 12 || 12;
  return `${hour}:${String(minutes).padStart(2, "0")} ${period}`;
}

export function formatTimeRange(meeting: Meeting): string {
  if (!meeting.startTime || !meeting.endTime) return "Time arranged";
  return `${formatTime(meeting.startTime).replace(/ (AM|PM)$/, "")}–${formatTime(meeting.endTime)}`;
}

export function formatMeetingDays(days: MeetingDay[]): string {
  return days.length ? days.join(" ") : "Async";
}

export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  if (!hours) return `${remainder}m`;
  if (!remainder) return `${hours}h`;
  return `${hours}h ${remainder}m`;
}

export function getVisibleScheduleRange(sections: Section[]): VisibleScheduleRange {
  const meetings = sections.flatMap((section) =>
    section.meetings.filter((meeting) => meeting.startTime && meeting.endTime),
  );
  if (!meetings.length) return { start: 7 * 60, end: 21 * 60 };
  const earliest = Math.min(...meetings.map((meeting) => minutesFromTime(meeting.startTime!)));
  const latest = Math.max(...meetings.map((meeting) => minutesFromTime(meeting.endTime!)));
  const start = Math.max(6 * 60, Math.floor(earliest / 60) * 60 - 60);
  const end = Math.min(22 * 60, Math.ceil(latest / 60) * 60 + 60);
  return end - start < 6 * 60 ? { start, end: Math.min(22 * 60, start + 6 * 60) } : { start, end };
}

export function getTimePosition(time: string, range: VisibleScheduleRange): number {
  return getTimeRatio(minutesFromTime(time), range) * 100;
}

export function getTimeRatio(minutes: number, range: VisibleScheduleRange): number {
  const duration = Math.max(1, range.end - range.start);
  return Math.max(0, Math.min(1, (minutes - range.start) / duration));
}

export function getTimeWidth(
  startTime: string,
  endTime: string,
  range: VisibleScheduleRange,
): number {
  const duration = Math.max(1, range.end - range.start);
  return Math.max(0, Math.min(100, ((minutesFromTime(endTime) - minutesFromTime(startTime)) / duration) * 100));
}

function dateRangesOverlap(a: Meeting, b: Meeting): boolean {
  if (!a.startDate || !a.endDate || !b.startDate || !b.endDate) return true;
  return a.startDate <= b.endDate && b.startDate <= a.endDate;
}

export function findSectionConflicts(
  candidate: Section,
  selected: Section[],
): ScheduleConflict[] {
  const conflicts: ScheduleConflict[] = [];
  for (const candidateMeeting of candidate.meetings) {
    if (!candidateMeeting.startTime || !candidateMeeting.endTime) continue;
    for (const existing of selected) {
      if (existing.id === candidate.id) continue;
      for (const existingMeeting of existing.meetings) {
        if (!existingMeeting.startTime || !existingMeeting.endTime) continue;
        const days = candidateMeeting.days.filter((day) => existingMeeting.days.includes(day));
        if (!days.length || !dateRangesOverlap(candidateMeeting, existingMeeting)) continue;
        const candidateStart = minutesFromTime(candidateMeeting.startTime);
        const candidateEnd = minutesFromTime(candidateMeeting.endTime);
        const existingStart = minutesFromTime(existingMeeting.startTime);
        const existingEnd = minutesFromTime(existingMeeting.endTime);
        if (candidateStart < existingEnd && candidateEnd > existingStart) {
          conflicts.push({
            candidateId: candidate.id,
            existingId: existing.id,
            existingCourseId: existing.courseId,
            days,
            overlapMinutes: Math.min(candidateEnd, existingEnd) - Math.max(candidateStart, existingStart),
            candidateStart: candidateMeeting.startTime,
            candidateEnd: candidateMeeting.endTime,
            existingStart: existingMeeting.startTime,
            existingEnd: existingMeeting.endTime,
          });
        }
      }
    }
  }
  return conflicts;
}

export function scheduleConflictCount(selected: Section[]): number {
  const pairs = new Set<string>();
  selected.forEach((section, index) => {
    findSectionConflicts(section, selected.slice(0, index)).forEach((conflict) => {
      pairs.add([conflict.candidateId, conflict.existingId].sort().join(":"));
    });
  });
  return pairs.size;
}

export function calculateCredits(selected: Section[], courses: Course[]): number {
  return selected.reduce(
    (total, section) => total + (courses.find((course) => course.id === section.courseId)?.credits ?? 0),
    0,
  );
}

export function courseCode(course: Course): string {
  return `${course.subject} ${course.courseNumber}`;
}

function sectionMatchesFilters(section: Section, filters: PlannerFilters): boolean {
  if (filters.openOnly && section.status !== "open") return false;
  if (filters.onlineOnly && section.modality !== "Online") return false;
  const meetingDays = new Set(section.meetings.flatMap((meeting) => meeting.days));
  if (filters.days.length && !filters.days.every((day) => meetingDays.has(day))) return false;
  if (filters.time !== "any") {
    const starts = section.meetings.flatMap((meeting) => meeting.startTime ? [minutesFromTime(meeting.startTime)] : []);
    if (!starts.length) return false;
    if (filters.time === "morning" && !starts.some((time) => time < 720)) return false;
    if (filters.time === "afternoon" && !starts.some((time) => time >= 720 && time < 1020)) return false;
    if (filters.time === "evening" && !starts.some((time) => time >= 1020)) return false;
  }
  return true;
}

export function searchCourses(
  courses: Course[],
  query: string,
  filters: PlannerFilters,
): Course[] {
  const normalized = query.trim().toLowerCase().replace(/\s+/g, " ");
  return courses.flatMap((course) => {
    const courseText = `${course.subject} ${course.courseNumber} ${course.title}`.toLowerCase();
    const courseMatches = !normalized || courseText.includes(normalized);
    const sections = course.sections.filter((section) => {
      const instructorMatches = (section.instructor ?? "").toLowerCase().includes(normalized);
      return (courseMatches || instructorMatches) && sectionMatchesFilters(section, filters);
    });
    return sections.length ? [{ ...course, sections }] : [];
  });
}

export function getCourse(courses: Course[], courseId: string): Course | undefined {
  return courses.find((course) => course.id === courseId);
}
