import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { DevelopmentStoryPage } from "./DevelopmentStoryPage";
import { projectUpdates } from "./model";

function renderStory(hash = "") {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: String(query).includes("prefers-reduced-motion"),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
  Element.prototype.scrollIntoView = () => undefined;
  window.scrollTo = () => undefined;
  return render(
    <MemoryRouter initialEntries={[{ pathname: "/updates", hash }]}>
      <DevelopmentStoryPage />
    </MemoryRouter>,
  );
}

describe("DevelopmentStoryPage", () => {
  it("orients the reader without opening the ledger", () => {
    renderStory();
    expect(screen.getByRole("heading", { name: /Built in public/i })).toBeInTheDocument();
    expect(screen.getAllByText(String(projectUpdates.length)).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Recorded events").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Technology used to build the system/i })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: /Automatic record update status/i })).toHaveTextContent(
      /Ticket 107 · AUG 20, 2026/i,
    );
    expect(screen.getByRole("heading", { name: /From idea to project/i })).toBeInTheDocument();
    expect(screen.queryByText(/email:/i)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/@[A-Z0-9.-]+\.[A-Z]{2,}/i);
  });

  it("opens and closes a chapter from the keyboard", () => {
    renderStory();
    const chapter = screen.getByRole("button", { name: /Building the foundation/i });
    expect(chapter).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(chapter);
    expect(chapter).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(/When the initial backend submission used Django/i)).toBeInTheDocument();
    fireEvent.click(chapter);
    expect(chapter).toHaveAttribute("aria-expanded", "false");
  }, 15000);

  it("opens a hashed chapter and event", async () => {
    renderStory("#ticket-87");
    const event = await screen.findByRole("button", {
      name: /Answered the question students actually asked/i,
    });
    expect(event).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByText("fddcb13").length).toBeGreaterThan(0);
  }, 15000);

  it("searches the full record", () => {
    renderStory();
    const search = screen.getByRole("searchbox");
    fireEvent.change(search, { target: { value: "ChromaDB" } });
    expect(screen.getAllByText(/ChromaDB/i).length).toBeGreaterThan(0);
    fireEvent.change(search, { target: { value: "fddcb13" } });
    expect(screen.getByRole("button", { name: /Answered the question students actually asked/i })).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "Evan" } });
    expect(screen.getAllByText(/Evan/i).length).toBeGreaterThan(0);
    fireEvent.change(search, { target: { value: "PostgreSQL" } });
    expect(screen.getByRole("heading", { name: /Putting Class Planner on production data/i })).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "June 30" } });
    expect(screen.getByRole("heading", { name: /Making \/ask work/i })).toBeInTheDocument();
  });

  it("filters by area and can clear the empty state", () => {
    renderStory();
    const filters = screen.getByRole("toolbar", { name: "Filter by area" });
    fireEvent.click(within(filters).getByRole("button", { name: "Class Planner" }));
    expect(screen.getByRole("heading", { name: /Putting Class Planner on production data/i })).toBeInTheDocument();
    fireEvent.click(within(filters).getByRole("button", { name: "Docs" }));
    expect(screen.getByRole("heading", { name: /Making the project transferable/i })).toBeInTheDocument();
    fireEvent.click(within(filters).getByRole("button", { name: "Frontend" }));
    expect(screen.getByRole("heading", { name: /Making \/ask work/i })).toBeInTheDocument();
    fireEvent.click(within(filters).getByRole("button", { name: "Backend" }));
    expect(screen.getAllByText(/of \d+ recorded events match/i).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Clear search and filters" }));
    expect(screen.getByRole("heading", { name: /From idea to project/i })).toBeInTheDocument();
  }, 15000);

  it("shows a no-result state for unmatched search", () => {
    renderStory();
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "zzzxnotarealquery" } });
    expect(screen.getByText("No recorded development events match this search.")).toBeInTheDocument();
  });

  it("can expand an event inside an open chapter", () => {
    renderStory();
    fireEvent.click(screen.getByRole("button", { name: /From idea to project/i }));
    const event = screen.getByRole("button", { name: /Elected as Project Manager of AskMcNeese/i });
    fireEvent.click(event);
    const detail = document.getElementById("ticket-1-panel");
    expect(within(detail as HTMLElement).getByText(/Prince Pudasaini/)).toBeInTheDocument();
  }, 15000);

  it("shows implementation technology separately from delivery tooling", () => {
    renderStory();
    fireEvent.click(screen.getByRole("button", { name: /Building the foundation/i }));
    fireEvent.click(
      screen.getByRole("button", {
        name: /Built and proved the Sprint 1 backend retrieval pipeline/i,
      }),
    );
    const detail = document.getElementById("ticket-18-panel") as HTMLElement;
    expect(within(detail).getByText("Python")).toBeInTheDocument();
    expect(within(detail).getByText("ChromaDB")).toBeInTheDocument();
    expect(within(detail).getByText("Git / GitHub")).toBeInTheDocument();
    expect(within(detail).getByText(/Delivery method \/ tooling/i)).toBeInTheDocument();
  }, 15000);

  it("keeps ACM Panel language separate from Ask retrieval", () => {
    renderStory();
    fireEvent.click(screen.getByRole("button", { name: /Wider retrieval and system governance/i }));
    expect(screen.getByText(/ACM Panel remained a separate chapter-management system/i)).toBeInTheDocument();
    expect(screen.getAllByText(/not part of Ask retrieval/i).length).toBeGreaterThan(0);
  });
});
