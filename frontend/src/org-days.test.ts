import { describe, expect, it } from "vitest";
import { daysInRole, formatDaysInRole } from "./content/orgChart";

describe("daysInRole", () => {
  it("counts inclusive days for an active tenure through today", () => {
    expect(
      daysInRole({ startDate: "2026-06-08" }, new Date(2026, 6, 15)),
    ).toBe(38); // June 8 → July 15 inclusive
  });

  it("counts inclusive days for a former tenure with endDate", () => {
    expect(
      daysInRole({ startDate: "2026-06-08", endDate: "2026-07-02" }),
    ).toBe(25); // June 8 → July 2 inclusive
  });

  it("returns 1 on the start day", () => {
    expect(daysInRole({ startDate: "2026-07-02" }, new Date(2026, 6, 2))).toBe(1);
  });

  it("formats singular and plural", () => {
    expect(formatDaysInRole(1)).toBe("1 day");
    expect(formatDaysInRole(25)).toBe("25 days");
  });
});
