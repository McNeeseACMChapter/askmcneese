import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { DEVELOPMENT_CHAPTERS } from "./chapters";
import {
  developmentChapters,
  eventMatchesQuery,
  projectUpdates,
  recordFreshness,
} from "./model";
import {
  assignedTicketNumbers,
  chapterIdForTicket,
  parseContributors,
  recordsFromCsv,
  stripPrivateData,
} from "./parseTimeline";

const timelinePath = path.resolve(process.cwd(), "../docs/pm/timeline.csv");

describe("canonical development record", () => {
  it("loads every timeline ticket exactly once into chapters", () => {
    const tickets = projectUpdates.map((event) => event.ticketNo).sort((a, b) => a - b);
    const assigned = assignedTicketNumbers();
    const expected = Array.from({ length: tickets[tickets.length - 1] }, (_, i) => i + 1);

    expect(tickets).toEqual(expected);
    expect(assigned).toEqual(expected);
    expect(new Set(assigned).size).toBe(assigned.length);
    expect(projectUpdates).toHaveLength(expected.length);
  });

  it("keeps known anchor facts exact", () => {
    const byTicket = Object.fromEntries(projectUpdates.map((event) => [event.ticketNo, event]));
    expect(byTicket[1].date).toBe("2026-03-25");
    expect(byTicket[29].date).toBe("2026-06-30");
    expect(byTicket[77].date).toBe("2026-08-09");
    expect(byTicket[87].date).toBe("2026-08-16");
    expect(byTicket[87].commit).toBe("fddcb13");
    expect(byTicket[106].date).toBe("2026-08-17");
    expect(byTicket[107].date).toBe("2026-08-20");
  });

  it("derives record freshness from the latest verified event", () => {
    expect(recordFreshness).toEqual({
      date: "2026-08-20",
      ticketNo: 107,
      title: projectUpdates.find((event) => event.ticketNo === 107)?.title,
    });
  });

  it("separates implementation technology from delivery tooling", () => {
    const byTicket = Object.fromEntries(projectUpdates.map((event) => [event.ticketNo, event]));

    expect(byTicket[1].technologies).toEqual([]);
    expect(byTicket[18].technologies).toEqual(
      expect.arrayContaining(["Python", "ChromaDB", "Git / GitHub"]),
    );
    expect(byTicket[18].technologies).not.toContain("Anthropic Claude");
    expect(byTicket[19].technologies).toContain("FastAPI");
    expect(byTicket[30].technologies).toEqual(
      expect.arrayContaining(["React", "TypeScript", "Vite", "Framer Motion"]),
    );
    expect(byTicket[77].technologies).toEqual(
      expect.arrayContaining(["PostgreSQL", "FastAPI", "React"]),
    );
    expect(byTicket[89].technologies).toContain("Plain text / Markdown");
  });

  it("assigns ticket 26 to the /ask chapter and 27–28 to foundation", () => {
    expect(chapterIdForTicket(26)).toBe("ask-pipeline");
    expect(chapterIdForTicket(27)).toBe("foundation");
    expect(chapterIdForTicket(28)).toBe("foundation");
    expect(chapterIdForTicket(87)).toBe("grounding");
    expect(chapterIdForTicket(88)).toBe("transition");
  });

  it("matches the generated model to the canonical CSV on disk", () => {
    const csv = readFileSync(timelinePath, "utf8");
    const records = recordsFromCsv(csv);
    expect(records.map((record) => record.ticketNo)).toEqual(
      projectUpdates.map((event) => event.ticketNo),
    );
    expect(records.map((record) => record.date)).toEqual(projectUpdates.map((event) => event.date));
    expect(records.map((record) => record.title)).toEqual(projectUpdates.map((event) => event.title));
  });

  it("strips private email addresses from notes", () => {
    const cleaned = stripPrivateData(
      "Prince assumed remaining roles; email: princepdsn@gmail.com",
    );
    expect(cleaned).not.toMatch(/@/);
    expect(cleaned).not.toMatch(/princepdsn/i);
    expect(projectUpdates.some((event) => /@/.test(event.notes ?? ""))).toBe(false);
  });

  it("preserves contributor attribution from the Who column", () => {
    const ticket30 = projectUpdates.find((event) => event.ticketNo === 30);
    const ticket6 = projectUpdates.find((event) => event.ticketNo === 6);
    const ticket88 = projectUpdates.find((event) => event.ticketNo === 88);
    expect(ticket30?.contributors.map((contributor) => contributor.name)).toEqual([
      "Evan Weber",
      "Prince",
    ]);
    expect(ticket6?.notes).toMatch(/Landon \(Backend\)/);
    expect(ticket6?.notes).toMatch(/Evan Weber \(Frontend\)/);
    expect(ticket88?.notes).toMatch(/Evan Weber continues Frontend/);
    expect(parseContributors("Prince Pudasaini (PM/Full Stack) + Ziyan (collaboration)")).toEqual([
      { name: "Prince Pudasaini", role: "PM/Full Stack" },
      { name: "Ziyan", role: "collaboration" },
    ]);
  });

  it("keeps eleven chapters covering every ticket", () => {
    expect(developmentChapters).toHaveLength(11);
    expect(DEVELOPMENT_CHAPTERS.flatMap((chapter) => chapter.ticketIds).sort((a, b) => a - b)).toEqual(
      assignedTicketNumbers(),
    );
  });

  it("finds representative searches across the record", () => {
    const queries = ["ChromaDB", "Class Planner", "fddcb13", "Evan", "RCCS", "PostgreSQL", "SSE", "June 30", "source registry", "CI", "mobile"];
    for (const query of queries) {
      const hits = projectUpdates.filter((event) =>
        eventMatchesQuery(event, query, developmentChapters.find((chapter) => chapter.id === event.chapterId)),
      );
      expect(hits.length, query).toBeGreaterThan(0);
    }
  });
});
