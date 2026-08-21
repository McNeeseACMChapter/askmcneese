import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchPlannerCourseSections,
  fetchPlannerSection,
  resolvePlannerDataMode,
  searchPlannerCourses,
} from "./plannerApi";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("planner API data source", () => {
  it("always resolves to an API-backed data mode", () => {
    expect(resolvePlannerDataMode(undefined, "production")).toBe("live");
    expect(resolvePlannerDataMode("mock", "production")).toBe("live");
    expect(resolvePlannerDataMode("staging", "production")).toBe("staging");
    expect(resolvePlannerDataMode(undefined, "development")).toBe("staging");
    expect(resolvePlannerDataMode(undefined, "test")).toBe("staging");
  });

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

  it("loads section detail in bounded six-item pages", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      data: { sections: [], total: 13, limit: 6, offset: 6, hasMore: true, nextOffset: 12 },
      source: { name: "McNeese Class Search" },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const response = await fetchPlannerCourseSections(
      "202660", "202660:ENGL:100", ["202660:61154"], 6,
    );
    const requested = new URL(String(fetchMock.mock.calls[0][0]));
    expect(requested.pathname).toBe("/class-planner/courses/202660%3AENGL%3A100/sections");
    expect(Object.fromEntries(requested.searchParams)).toMatchObject({
      term: "202660",
      limit: "6",
      offset: "6",
      selected: "202660:61154",
    });
    expect(response.data.nextOffset).toBe(12);
  });

  it("requests targeted verification before Add", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      data: { id: "202660:61154", termId: "202660", courseId: "202660:CSCI:308" },
      source: { name: "McNeese Class Search" },
      verification: { status: "unavailable", updated: 0 },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const response = await fetchPlannerSection("202660:61154", undefined, true);
    const requested = new URL(String(fetchMock.mock.calls[0][0]));
    expect(requested.searchParams.get("verify")).toBe("true");
    expect(response.verification?.status).toBe("unavailable");
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

