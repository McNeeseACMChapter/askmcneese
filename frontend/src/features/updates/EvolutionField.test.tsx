import { fireEvent, render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { developmentChapters, projectUpdates } from "./model";
import {
  buildContributionCalendar,
  contributionLevel,
  EvolutionField,
} from "./EvolutionField";

beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

describe("development contribution calendar", () => {
  it("maps the complete canonical date range into GitHub-style weeks", () => {
    const calendar = buildContributionCalendar(projectUpdates);

    expect(calendar.firstDate).toBe("2026-03-25");
    expect(calendar.lastDate).toBe("2026-08-20");
    expect(calendar.weekCount).toBe(22);
    expect(calendar.cells).toHaveLength(154);
    expect(calendar.cells.filter((cell) => cell.inRange)).toHaveLength(149);
    expect(calendar.months).toEqual([
      { label: "Apr", weekIndex: 1 },
      { label: "May", weekIndex: 5 },
      { label: "Jun", weekIndex: 10 },
      { label: "Jul", weekIndex: 14 },
      { label: "Aug", weekIndex: 18 },
    ]);

    expect(calendar.cells.find((cell) => cell.date === "2026-03-25")).toMatchObject({
      weekIndex: 0,
      weekdayIndex: 3,
    });
    expect(calendar.cells.find((cell) => cell.date === "2026-08-20")).toMatchObject({
      weekIndex: 21,
      weekdayIndex: 4,
    });
    expect(calendar.cells.find((cell) => cell.date === "2026-08-16")?.events).toHaveLength(16);
  });

  it("uses stable event-density thresholds", () => {
    expect([0, 1, 2, 3, 4, 7, 8].map(contributionLevel)).toEqual([0, 1, 2, 2, 3, 3, 4]);
  });

  it("supports keyboard navigation and daily event drill-down", () => {
    const onOpenTicket = vi.fn();
    render(
      <EvolutionField
        chapters={developmentChapters}
        events={projectUpdates}
        activeChapterId={null}
        matchingTicketNos={new Set(projectUpdates.map((event) => event.ticketNo))}
        onOpenTicket={onOpenTicket}
      />,
    );

    expect(screen.getByRole("grid", { name: /22-week project contribution calendar/i })).toBeInTheDocument();
    const latestDay = screen.getByRole("gridcell", { name: /Thursday, August 20, 2026 — 1 recorded event/i });
    latestDay.focus();
    fireEvent.keyDown(latestDay, { key: "ArrowLeft" });
    expect(document.activeElement).toHaveAttribute("data-date", "2026-08-13");

    fireEvent.click(latestDay);
    expect(screen.getByRole("heading", { name: /Thursday, August 20, 2026/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: /ticket 107/i }));
    expect(onOpenTicket).toHaveBeenCalledWith(107);
  }, 15000);
});
