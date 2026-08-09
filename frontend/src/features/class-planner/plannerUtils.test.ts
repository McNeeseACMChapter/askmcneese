import { describe, expect, it } from "vitest";
import { PLANNER_COURSES } from "./plannerData";
import type { MeetingDay, Section } from "./plannerTypes";
import {
  calculateCredits, findSectionConflicts, formatDuration, getTimePosition, getTimeRatio, getTimeWidth,
  getVisibleScheduleRange, searchCourses,
} from "./plannerUtils";

const filters = { openOnly: false, onlineOnly: false, days: [], time: "any" as const };

describe("class planner utilities", () => {
  it("searches by code, title, and instructor while preserving course groups", () => {
    expect(searchCourses(PLANNER_COURSES, "CSCI 308", filters)[0].sections).toHaveLength(4);
    expect(searchCourses(PLANNER_COURSES, "Calculus", filters)[0].id).toBe("math-191");
    const instructorResult = searchCourses(PLANNER_COURSES, "Thibodeaux", filters)[0];
    expect(instructorResult.id).toBe("csci-308");
    expect(instructorResult.sections.map((section) => section.id)).toEqual(["csci-308-002"]);
  });

  it("matches requested days across lecture and lab components", () => {
    const compoundDays = { ...filters, days: ["M", "R"] as MeetingDay[] };
    const result = searchCourses(PLANNER_COURSES, "MATH 191", compoundDays);
    expect(result[0].sections.map((section) => section.id)).toContain("math-191-001");
  });

  it("detects the exact overlap and common days", () => {
    const candidate = PLANNER_COURSES[1].sections[0];
    const existing = PLANNER_COURSES[0].sections[0];
    const conflict = findSectionConflicts(candidate, [existing])[0];
    expect(conflict.overlapMinutes).toBe(20);
    expect(conflict.days).toEqual(["M", "W", "F"]);
  });

  it("allows classes that touch at an exact boundary", () => {
    const existing = PLANNER_COURSES[0].sections[0];
    const boundary: Section = {
      ...PLANNER_COURSES[1].sections[0],
      id: "boundary",
      meetings: [{ type: "Lecture", days: ["M"], startTime: "10:50", endTime: "11:40" }],
    };
    expect(findSectionConflicts(boundary, [existing])).toEqual([]);
  });

  it("counts course credits from selected sections", () => {
    expect(calculateCredits(
      [PLANNER_COURSES[0].sections[0], PLANNER_COURSES[1].sections[1]],
      PLANNER_COURSES,
    )).toBe(7);
  });

  it("derives a padded visible range and normalized horizontal geometry", () => {
    const sections = [PLANNER_COURSES[0].sections[0]];
    const range = getVisibleScheduleRange(sections);
    expect(range).toEqual({ start: 9 * 60, end: 15 * 60 });
    expect(getTimePosition("12:00", range)).toBe(50);
    expect(getTimeWidth("13:00", "13:50", range)).toBeCloseTo(13.889, 2);
  });

  it("uses the default academic range when all meetings are flexible", () => {
    expect(getVisibleScheduleRange([PLANNER_COURSES[4].sections[0]])).toEqual({
      start: 7 * 60,
      end: 21 * 60,
    });
  });

  it("uses one exact 7 AM–10 PM coordinate scale for Week Pulse geometry", () => {
    const range = { start: 7 * 60, end: 22 * 60 };
    expect(getTimeRatio(7 * 60, range)).toBe(0);
    expect(getTimeRatio(14 * 60 + 30, range)).toBe(0.5);
    expect(getTimeRatio(22 * 60, range)).toBe(1);
    expect(getTimePosition("14:30", range)).toBe(50);

    const fiftyMinutes = getTimeWidth("10:00", "10:50", range);
    const seventyFiveMinutes = getTimeWidth("10:00", "11:15", range);
    const oneHundredSixtyFiveMinutes = getTimeWidth("10:00", "12:45", range);
    expect(fiftyMinutes).toBeLessThan(seventyFiveMinutes);
    expect(seventyFiveMinutes).toBeLessThan(oneHundredSixtyFiveMinutes);
  });

  it("formats timeline gaps without inventing precision", () => {
    expect(formatDuration(20)).toBe("20m");
    expect(formatDuration(60)).toBe("1h");
    expect(formatDuration(285)).toBe("4h 45m");
  });
});
