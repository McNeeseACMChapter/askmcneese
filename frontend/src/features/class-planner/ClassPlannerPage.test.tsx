import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  classPlannerShareUrl,
  ClassPlannerPage,
  formatPlannerFreshness,
} from "./ClassPlannerPage";
import * as persistence from "./plannerPersistence";
import { TEST_PLANNER_COURSES } from "../../../test-fixtures/plannerCourses";
import type { Course, Section } from "./plannerTypes";

const TEST_SOURCE = {
  name: "McNeese Class Search",
  fetchedAt: "2026-08-08T12:00:00Z",
  metadataVerifiedAt: "2026-08-08T12:00:00Z",
  availabilityVerifiedAt: "2026-08-08T12:00:00Z",
  mode: "staging",
} as const;

function plannerResponse(data: unknown, extra: Record<string, unknown> = {}) {
  return new Response(JSON.stringify({ data, source: TEST_SOURCE, ...extra }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function apiSection(course: Course, section: Section) {
  return {
    ...section,
    credits: course.credits,
    subject: course.subject,
    courseNumber: course.courseNumber,
    title: course.title,
  };
}

function installPlannerApiFixture() {
  vi.stubGlobal("fetch", vi.fn(async (request: string | URL | Request) => {
    const requestUrl = request instanceof Request ? request.url : String(request);
    const url = new URL(requestUrl, window.location.origin);

    if (url.pathname === "/class-planner/courses") {
      const query = (url.searchParams.get("q") ?? "").trim().toLowerCase();
      const compactQuery = query.replace(/\s+/g, "");
      const matches = TEST_PLANNER_COURSES.filter((course) => {
        const code = `${course.subject}${course.courseNumber}`.toLowerCase();
        return !query
          || code.includes(compactQuery)
          || course.title.toLowerCase().includes(query)
          || course.sections.some((section) => section.instructor?.toLowerCase().includes(query));
      }).map((course) => ({
        ...course,
        sections: [],
        sectionCount: course.sections.length,
        openCount: course.sections.filter((section) => section.status === "open").length,
      }));
      return plannerResponse(matches);
    }

    const courseMatch = url.pathname.match(/^\/class-planner\/courses\/([^/]+)\/sections$/);
    if (courseMatch) {
      const course = TEST_PLANNER_COURSES.find((item) => item.id === decodeURIComponent(courseMatch[1]));
      if (!course) return new Response(null, { status: 404 });
      const sections = course.sections.map((section) => apiSection(course, section));
      return plannerResponse({
        sections,
        total: sections.length,
        limit: 6,
        offset: 0,
        hasMore: false,
        nextOffset: null,
      });
    }

    const sectionMatch = url.pathname.match(/^\/class-planner\/sections\/([^/]+)$/);
    if (sectionMatch) {
      const sectionId = decodeURIComponent(sectionMatch[1]);
      for (const course of TEST_PLANNER_COURSES) {
        const section = course.sections.find((item) => item.id === sectionId);
        if (section) return plannerResponse(apiSection(course, section), { verification: { status: "verified" } });
      }
      return new Response(null, { status: 404 });
    }

    return new Response(null, { status: 404 });
  }));
}

describe("ClassPlannerPage", { timeout: 15_000 }, () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    installPlannerApiFixture();
    window.localStorage.clear();
    Object.defineProperty(window.navigator, "onLine", { configurable: true, value: true });
    Object.defineProperty(window.navigator, "share", { configurable: true, value: undefined });
  });

  it("keeps shared links on Class Planner and formats exact freshness", () => {
    expect(classPlannerShareUrl("https://ask.mcneeseacm.com/ask?thread=123")).toBe(
      "https://ask.mcneeseacm.com/class-planner",
    );
    expect(
      formatPlannerFreshness(
        "2026-08-21T00:10:25.083846+00:00",
        new Date("2026-08-21T00:20:00Z"),
      ),
    ).toBe("Checked today · Aug 20, 2026, 7:10 PM");
  });

  it("keeps mobile tabs Week then Find and defaults from saved schedule state", () => {
    const first = render(<ClassPlannerPage />);
    expect(screen.getAllByRole("tab").map((tab) => tab.textContent)).toEqual(["Week", "Find"]);
    expect(screen.getByRole("tab", { name: "Find" })).toHaveAttribute("aria-selected", "true");
    first.unmount();

    window.localStorage.setItem(
      "askmcneese.class-planner.v1.202660",
      JSON.stringify(["csci-308-001"]),
    );
    render(<ClassPlannerPage />);
    expect(screen.getByRole("tab", { name: /Week/ })).toHaveAttribute("aria-selected", "true");
  });

  it("finds grouped sections, adds a fitting section, and updates totals", async () => {
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await user.type(screen.getByRole("searchbox"), "CSCI 308");
    const course = await screen.findByRole("button", { name: /CSCI 308.*Software Engineering/i });
    expect(screen.getByText("1 course")).toBeInTheDocument();
    expect(screen.getByText(/Checked Aug 8, 2026, 7:00 AM/)).toBeInTheDocument();
    await user.click(course);
    await screen.findAllByRole("button", { name: "Add" });
    expect(screen.getAllByText("Aug 24 – Dec 7, 2026").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Fits your week/i).length).toBeGreaterThan(0);
    await user.click(screen.getAllByRole("button", { name: "Add" })[0]);
    await waitFor(() => expect(screen.getAllByText(/1 class · 3 credits/i)).toHaveLength(2));
    expect(window.localStorage.getItem("askmcneese.class-planner.v1.202660")).toContain("csci-308-001");
  });

  it("allows a zero-seat section in the planning schedule", async () => {
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await user.type(screen.getByRole("searchbox"), "CSCI 308");
    await user.click(await screen.findByRole("button", { name: /CSCI 308.*Software Engineering/i }));

    const seatNotice = screen.getByText("No seats open · You can still add this to your plan");
    const sectionCard = seatNotice.closest("article") as HTMLElement;
    const add = within(sectionCard).getByRole("button", { name: "Add" });
    expect(add).toBeEnabled();

    await user.click(add);

    expect(window.localStorage.getItem("askmcneese.class-planner.v1.202660")).toContain("csci-308-004");
    expect(screen.getByText(/No seats are currently open; Class Planner does not register classes/i)).toBeInTheDocument();
  });

  it("shows every distinct meeting pattern before a section is added", async () => {
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await user.type(screen.getByRole("searchbox"), "MATH 191");
    await user.click(await screen.findByRole("button", { name: /MATH 191.*Calculus I/i }));

    const schedule = await screen.findByRole("group", { name: "Section 001 meeting schedule" });
    expect(schedule).toHaveTextContent(/M W F.*10:30–11:20 AM.*Lecture.*Kirkman 105/i);
    expect(schedule).toHaveTextContent(/R.*2:00–2:50 PM.*Lab.*Kirkman 112/i);
  });

  it("keeps a mobile Ask shortcut available from Class Planner", () => {
    render(<ClassPlannerPage />);
    expect(screen.getByRole("link", { name: "Ask McNeese about classes" })).toHaveAttribute(
      "href",
      "/ask",
    );
  });

  it("shares the Class Planner route without leaking the current page state", async () => {
    const share = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window.navigator, "share", { configurable: true, value: share });
    const user = userEvent.setup();
    render(<ClassPlannerPage />);

    await user.click(screen.getByRole("button", { name: "Share Class Planner" }));

    expect(share).toHaveBeenCalledWith({
      title: "AskMcNeese Class Planner",
      text: "Search Fall 2026 classes and build a weekly schedule.",
      url: classPlannerShareUrl(window.location.origin),
    });
  });

  it("blocks a conflicting add and explains the overlap", async () => {
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await user.type(screen.getByRole("searchbox"), "CSCI 308");
    await user.click(await screen.findByRole("button", { name: /CSCI 308.*Software Engineering/i }));
    await user.click((await screen.findAllByRole("button", { name: "Add" }))[0]);

    await user.clear(screen.getByRole("searchbox"));
    await user.type(screen.getByRole("searchbox"), "MATH 191");
    await user.click(await screen.findByRole("button", { name: /MATH 191.*Calculus I/i }));
    await user.click((await screen.findAllByRole("button", { name: "Add" }))[0]);
    const dialog = await screen.findByRole("dialog", { name: /These sections overlap/i });
    expect(within(dialog).getByText(/Overlap: 20 minutes/i)).toBeInTheDocument();
    expect(within(dialog).getByText("CSCI 308")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close conflict details" })).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: /These sections overlap/i })).not.toBeInTheDocument();
  });

  it("replaces an existing section of the same course instead of duplicating credits", async () => {
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await user.type(screen.getByRole("searchbox"), "CSCI 308");
    await user.click(await screen.findByRole("button", { name: /CSCI 308.*Software Engineering/i }));
    await user.click((await screen.findAllByRole("button", { name: "Add" }))[0]);
    await user.click((await screen.findAllByRole("button", { name: "Add" }))[0]);
    const persisted = window.localStorage.getItem("askmcneese.class-planner.v1.202660") ?? "";
    expect(persisted).not.toContain("csci-308-001");
    expect(persisted).toContain("csci-308-002");
    expect(screen.getAllByText(/1 class · 3 credits/i)).toHaveLength(2);
  });

  it("shows API CRNs and keeps official registration as the final step", async () => {
    window.localStorage.setItem("askmcneese.class-planner.v1.202660", JSON.stringify(["csci-308-001"]));
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await screen.findByText(/1 class · 3 credits/i);
    await user.click(screen.getByRole("button", { name: /Registration Summary/i }));
    expect(screen.getByRole("dialog", { name: "Registration Summary" })).toHaveTextContent("CRN 12345");
    expect(screen.queryByText(/Sample CRNs/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy CRNs" })).toBeEnabled();
    expect(screen.getByRole("button", { name: /Banner handoff requires live data/i })).toBeDisabled();
  });

  it("retries a failed persistence write", async () => {
    const save = vi.spyOn(persistence, "saveSchedule")
      .mockImplementationOnce(() => { throw new Error("storage blocked"); })
      .mockImplementationOnce(() => undefined);
    const user = userEvent.setup();
    render(<ClassPlannerPage />);
    await user.type(screen.getByRole("searchbox"), "ENGL 101");
    await user.click(await screen.findByRole("button", { name: /ENGL 101.*Academic Writing/i }));
    await user.click(await screen.findByRole("button", { name: "Add" }));
    expect(await screen.findByRole("heading", { name: /couldn't save/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(save).toHaveBeenCalledTimes(2);
    expect(screen.getByText("Schedule saved on this device.")).toBeInTheDocument();
  });

  it("only exposes the configured API-backed academic term", () => {
    render(<ClassPlannerPage />);
    const term = screen.getByRole("combobox", { name: "Academic term" });
    expect(within(term).getAllByRole("option")).toHaveLength(1);
    expect(term).toHaveValue("202660");
  });
  it("keeps the whole week visible while the selected day drives a timeline", async () => {
    window.localStorage.setItem(
      "askmcneese.class-planner.v1.202660",
      JSON.stringify(["csci-308-001", "math-191-002", "engl-101-001", "hist-201-090"]),
    );
    const user = userEvent.setup();
    const { container } = render(<ClassPlannerPage />);
    await user.click(screen.getByRole("tab", { name: /Week/ }));

    for (const day of ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]) {
      expect(screen.getByRole("button", { name: new RegExp(`^${day},`) })).toBeInTheDocument();
    }
    const today = screen.getByRole("button", { name: /^Thursday, August 20, 2026.*today/i });
    expect(today).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("heading", { name: "Thursday" })).toBeInTheDocument();
    expect(screen.getByText("Thursday, August 20, 2026 · Today")).toBeInTheDocument();
    expect(screen.getByText(/Fall classes begin August 24, 2026/i)).toBeInTheDocument();
    expect(Array.from(container.querySelectorAll<HTMLElement>(".weekPulseAxis small")).map((label) => label.style.left))
      .toEqual(["0%", "33.33333333333333%", "66.66666666666666%", "100%"]);

    await user.click(screen.getByRole("button", { name: "Next week" }));
    expect(screen.getByText("Aug 24–28, 2026")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /^CSCI 308, Monday/ })).toHaveStyle({
      left: "20%",
      width: "5.555555555555555%",
    });
    expect(container.querySelectorAll(".weekPulseSelection")).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: /^Tuesday, August 25, 2026/ }));
    expect(await screen.findByRole("heading", { name: "Tuesday" })).toBeInTheDocument();
    const tuesday = screen.getByRole("region", { name: "Tuesday" });
    expect(within(tuesday).getByText("Calculus I")).toBeInTheDocument();
    expect(within(tuesday).getByText("2 classes · 2h 5m")).toBeInTheDocument();
    expect(within(tuesday).getByText("4h 45m free")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Flexible" })).toBeInTheDocument();
    expect(screen.getByText("HIST 201")).toBeInTheDocument();

    await user.click(within(tuesday).getByRole("button", { name: /View MATH 191/ }));
    const detail = screen.getByRole("dialog", { name: "Calculus I" });
    expect(detail).toHaveTextContent("Section 002");
    expect(within(detail).getByRole("button", { name: "Remove from schedule" })).toBeInTheDocument();
  });
});
