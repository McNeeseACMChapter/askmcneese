import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchPlannerSection, searchPlannerCourses } from "./plannerApi";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("planner API data source", () => {
  it("sends deterministic search filters to AskMcNeese", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      data: [],
      source: { name: "McNeese Class Search", fetchedAt: "2026-08-08T14:00:00Z" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    await searchPlannerCourses("202660", "CSCI 308", {
      openOnly: true,
      onlineOnly: false,
      days: ["T", "R"],
      time: "evening",
    });

    const requested = new URL(String(fetchMock.mock.calls[0][0]));
    expect(requested.pathname).toBe("/class-planner/courses");
    expect(Object.fromEntries(requested.searchParams)).toMatchObject({
      term: "202660",
      q: "CSCI 308",
      open: "true",
      online: "false",
      days: "T,R",
      time: "evening",
    });
  });

  it("loads a canonical saved section without falling back to mock data", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      data: { id: "202660:61154", termId: "202660", courseId: "202660:CSCI:308" },
      source: { name: "McNeese Class Search" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const response = await fetchPlannerSection("202660:61154");
    expect(response.data.id).toBe("202660:61154");
    expect(response.source.name).toBe("McNeese Class Search");
  });
});

