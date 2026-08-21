import { describe, expect, it } from "vitest";
import { PLANNER_COURSES } from "./plannerData";
import {
  formatPlannerWeekRange,
  getMeetingTemporalInfo,
  getPlannerClockSnapshot,
  getPlannerWeekDates,
  isPlannerToday,
  meetingOccursOnPlannerDate,
} from "./plannerTime";

const mondayMeeting = PLANNER_COURSES[0].sections[0].meetings[0];

describe("planner live time", () => {
  it("derives McNeese-local date, weekday, and minutes in America/Chicago", () => {
    const clock = getPlannerClockSnapshot(new Date("2026-08-25T04:30:00Z"));
    expect(clock.currentDate).toBe("2026-08-24");
    expect(clock.currentWeekday).toBe("M");
    expect(clock.currentMinutes).toBe(23 * 60 + 30);
  });

  it("does not expose live state before, after, or during an excluded term date", () => {
    expect(getPlannerClockSnapshot(new Date("2026-08-23T15:00:00Z")).isTermActive).toBe(false);
    expect(getPlannerClockSnapshot(new Date("2026-12-08T16:00:00Z")).isTermActive).toBe(false);

    const laborDay = getPlannerClockSnapshot(new Date("2026-09-07T15:25:00Z"));
    expect(laborDay.isTermActive).toBe(true);
    expect(laborDay.isInstructionDay).toBe(false);
    expect(getMeetingTemporalInfo(mondayMeeting, laborDay).state).toBe("inactive");
  });

  it("marks the real weekday as today even before classes begin", () => {
    const thursday = getPlannerClockSnapshot(new Date("2026-08-21T00:10:00Z"));
    expect(thursday.currentDate).toBe("2026-08-20");
    expect(thursday.isInstructionDay).toBe(false);
    expect(isPlannerToday("R", thursday)).toBe(true);
  });

  it("builds dated current and next weeks in McNeese calendar order", () => {
    const currentWeek = getPlannerWeekDates("2026-08-20");
    expect(currentWeek.map((day) => day.date)).toEqual([
      "2026-08-17",
      "2026-08-18",
      "2026-08-19",
      "2026-08-20",
      "2026-08-21",
    ]);
    expect(formatPlannerWeekRange(currentWeek)).toBe("Aug 17–21, 2026");
    expect(getPlannerWeekDates("2026-08-20", 1)[0].date).toBe("2026-08-24");
  });

  it("filters recurring meetings by term dates and no-class dates", () => {
    expect(meetingOccursOnPlannerDate(mondayMeeting, "2026-08-17")).toBe(false);
    expect(meetingOccursOnPlannerDate(mondayMeeting, "2026-08-24")).toBe(true);
    expect(meetingOccursOnPlannerDate(mondayMeeting, "2026-09-07")).toBe(false);
  });

  it("deterministically distinguishes upcoming, current, and completed meetings", () => {
    const upcoming = getPlannerClockSnapshot(new Date("2026-08-24T13:30:00Z"));
    const current = getPlannerClockSnapshot(new Date("2026-08-24T15:25:00Z"));
    const completed = getPlannerClockSnapshot(new Date("2026-08-24T17:00:00Z"));

    expect(getMeetingTemporalInfo(mondayMeeting, upcoming)).toMatchObject({
      state: "upcoming",
      minutesUntilStart: 90,
    });
    expect(getMeetingTemporalInfo(mondayMeeting, current)).toMatchObject({
      state: "current",
      progress: 0.5,
      minutesRemaining: 25,
    });
    expect(getMeetingTemporalInfo(mondayMeeting, completed)).toMatchObject({
      state: "completed",
      progress: 1,
    });
  });

  it("keeps non-meeting weekdays and meeting date exclusions inactive", () => {
    const tuesday = getPlannerClockSnapshot(new Date("2026-08-25T15:25:00Z"));
    expect(getMeetingTemporalInfo(mondayMeeting, tuesday).state).toBe("inactive");

    const datedMeeting = {
      ...mondayMeeting,
      startDate: "2026-10-01",
      endDate: "2026-10-31",
    };
    const augustMonday = getPlannerClockSnapshot(new Date("2026-08-24T15:25:00Z"));
    expect(getMeetingTemporalInfo(datedMeeting, augustMonday).state).toBe("inactive");
  });

  it.each([
    ["07:00", "2026-08-24T12:00:00Z", 420],
    ["08:30", "2026-08-24T13:30:00Z", 510],
    ["12:00", "2026-08-24T17:00:00Z", 720],
    ["14:25", "2026-08-24T19:25:00Z", 865],
    ["18:30", "2026-08-24T23:30:00Z", 1110],
    ["21:59", "2026-08-25T02:59:00Z", 1319],
  ])("maps controlled time %s to exact local minutes", (_, iso, minutes) => {
    expect(getPlannerClockSnapshot(new Date(iso)).currentMinutes).toBe(minutes);
  });
});
