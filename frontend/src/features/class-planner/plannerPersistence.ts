import type { Course, Section } from "./plannerTypes";

const STORAGE_PREFIX = "askmcneese.class-planner.v1";

function storageKey(termId: string): string {
  return `${STORAGE_PREFIX}.${termId}`;
}

function snapshotKey(termId: string): string {
  return `${storageKey(termId)}.snapshot`;
}

export function getSchedule(termId: string, validSections: Section[]): Section[] {
  const ids = getScheduleIds(termId);
  const validById = new Map(validSections.map((section) => [section.id, section]));
  return ids.flatMap((id) => validById.has(id) ? [validById.get(id)!] : []);
}

export function getScheduleIds(termId: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    const ids = JSON.parse(window.localStorage.getItem(storageKey(termId)) ?? "[]");
    if (!Array.isArray(ids)) return [];
    return ids.filter((id): id is string => typeof id === "string");
  } catch {
    return [];
  }
}

export function getScheduleCache(termId: string): Course[] {
  if (typeof window === "undefined") return [];
  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(snapshotKey(termId)) ?? "[]");
    if (!Array.isArray(value)) return [];
    return value.filter((course): course is Course => (
      typeof course === "object"
      && course !== null
      && typeof (course as Course).id === "string"
      && Array.isArray((course as Course).sections)
    ));
  } catch {
    return [];
  }
}

export function saveSchedule(termId: string, sections: Section[], courses?: Course[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(storageKey(termId), JSON.stringify(sections.map((section) => section.id)));
  if (courses) {
    const selectedIds = new Set(sections.map((section) => section.id));
    const snapshot = courses.flatMap((course) => {
      const selectedSections = course.sections.filter((section) => selectedIds.has(section.id));
      return selectedSections.length ? [{ ...course, sections: selectedSections }] : [];
    });
    window.localStorage.setItem(snapshotKey(termId), JSON.stringify(snapshot));
  }
}
