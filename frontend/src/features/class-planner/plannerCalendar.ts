/**
 * Published Fall 2026 calendar boundaries used only for calendar rendering.
 * Course, section, CRN, instructor, meeting, and availability data always come
 * from the Class Planner API.
 */
export const PLANNER_TERM = {
  id: "202660",
  label: "Fall 2026",
  timezone: "America/Chicago",
  classStartDate: "2026-08-24",
  classEndDate: "2026-12-07",
  noClassDates: [
    "2026-09-07",
    "2026-10-08",
    "2026-10-09",
    "2026-11-25",
    "2026-11-26",
    "2026-11-27",
    "2026-11-28",
  ],
} as const;
