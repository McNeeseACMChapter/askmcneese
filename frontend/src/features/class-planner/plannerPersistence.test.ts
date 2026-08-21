import { beforeEach, describe, expect, it } from "vitest";
import type { Course, Section } from "./plannerTypes";
import { addScheduleSections, getScheduleCache, getScheduleIds, saveSchedule } from "./plannerPersistence";

function section(id: string, courseId: string, crn: string): Section {
  return {
    id,
    courseId,
    termId: "202660",
    crn,
    sectionNumber: "A",
    meetings: [],
    modality: "In person",
    seatsRemaining: 5,
    status: "open",
    updatedAt: "2026-08-14T12:00:00Z",
  };
}

function course(id: string, subject: string, courseNumber: string, selected: Section): Course {
  return { id, subject, courseNumber, title: `${subject} ${courseNumber}`, credits: 3, sections: [selected] };
}

describe("plannerPersistence handoff", () => {
  beforeEach(() => window.localStorage.clear());

  it("replaces an alternate section while preserving unrelated courses", () => {
    const oldCalculus = section("202660:61068", "202660:MATH:291", "61068");
    const biology = section("202660:62000", "202660:BIOL:102", "62000");
    saveSchedule("202660", [oldCalculus, biology], [
      course(oldCalculus.courseId, "MATH", "291", oldCalculus),
      course(biology.courseId, "BIOL", "102", biology),
    ]);

    const selectedCalculus = section("202660:61066", "202660:MATH:291", "61066");
    const selectedCsci = section("202660:61154", "202660:CSCI:308", "61154");
    addScheduleSections("202660", [selectedCalculus, selectedCsci]);

    expect(getScheduleIds("202660")).toEqual([
      "202660:62000",
      "202660:61066",
      "202660:61154",
    ]);
    expect(getScheduleCache("202660").map((item) => item.id)).toEqual([
      "202660:BIOL:102",
      "202660:MATH:291",
      "202660:CSCI:308",
    ]);
  });
});
