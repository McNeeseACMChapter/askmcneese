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

export function addScheduleSections(termId: string, sections: Section[]): void {
  if (typeof window === "undefined" || sections.length === 0) return;
  const existing = getScheduleCache(termId);
  const replacedCourseIds = new Set(sections.map((section) => section.courseId));
  const existingCourseBySection = new Map(
    existing.flatMap((course) => course.sections.map((section) => [section.id, course.id] as const)),
  );
  const retainedIds = getScheduleIds(termId).filter(
    (id) => !replacedCourseIds.has(existingCourseBySection.get(id) ?? ""),
  );
  const ids = Array.from(new Set([...retainedIds, ...sections.map((section) => section.id)]));
  window.localStorage.setItem(storageKey(termId), JSON.stringify(ids));

  // A polished plan has one selected section per course. Replace only courses
  // present in the handoff and leave every unrelated saved course untouched.
  const byCourse = new Map(
    existing
      .filter((course) => !replacedCourseIds.has(course.id))
      .map((course) => [course.id, course]),
  );
  sections.forEach((section) => {
    const course = byCourse.get(section.courseId);
    if (course) {
      if (!course.sections.some((item) => item.id === section.id)) {
        course.sections = [...course.sections, section];
      }
      return;
    }
    byCourse.set(section.courseId, {
      id: section.courseId,
      subject: String((section as Section & { subject?: string }).subject ?? ""),
      courseNumber: String((section as Section & { courseNumber?: string }).courseNumber ?? ""),
      title: String((section as Section & { title?: string }).title ?? "Course"),
      credits: Number(section.credits ?? 0),
      sections: [section],
    });
  });
  window.localStorage.setItem(snapshotKey(termId), JSON.stringify(Array.from(byCourse.values())));
}
