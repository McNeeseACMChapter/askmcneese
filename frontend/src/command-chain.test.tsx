import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CommandChain } from "./components/about/CommandChain";

describe("CommandChain", () => {
  it("renders the ACM, advisor, project manager, and builders hierarchy", () => {
    render(<CommandChain />);
    expect(screen.getByRole("heading", { name: /Who steers AskMcNeese/i })).toBeInTheDocument();
    expect(screen.getAllByText(/McNeese ACM/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Dr\. Vipin Menon/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Prince Pudasaini/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Landon Peurta/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Ziyan/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Evan Weber/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Kody Vo/i).length).toBeGreaterThan(0);
  });

  it("gives every contributor a selectable editorial profile", () => {
    render(<CommandChain />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(5);
    expect(tabs.map((tab) => tab.textContent)).toEqual([
      expect.stringContaining("Prince Pudasaini"),
      expect.stringContaining("Evan Weber"),
      expect.stringContaining("Ziyan"),
      expect.stringContaining("Dr. Vipin Menon"),
      expect.stringContaining("Landon Peurta"),
    ]);
    expect(tabs.filter((tab) => tab.getAttribute("aria-selected") === "true")).toHaveLength(1);

    const evanTab = screen.getByRole("tab", { name: /Evan Weber/i });
    fireEvent.click(evanTab);
    expect(evanTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel", { name: /Evan Weber/i })).toHaveTextContent(/Product experience/i);

    fireEvent.keyDown(evanTab, { key: "ArrowDown" });
    expect(screen.getByRole("tab", { name: /Ziyan/i })).toHaveAttribute("aria-selected", "true");
  });

  it("marks Landon as a former contributor without reducing his profile", () => {
    const { container } = render(<CommandChain />);
    expect(screen.getAllByText(/Former · June 8 – July 2/i).length).toBeGreaterThan(0);
    expect(container.querySelector(".about-member-tab__status.is-former")).toBeInTheDocument();
  });

  it("keeps keyboard stops limited to interactive controls", () => {
    const { container } = render(<CommandChain />);
    expect(container.querySelectorAll(".about-member-profile[tabindex]")).toHaveLength(0);
    expect(container.querySelectorAll(".about-governance-flow > div[tabindex]")).toHaveLength(0);
  });

  it("starts autoplay and lets a deliberate surface tap pause and resume it", () => {
    const { container } = render(<CommandChain />);
    const stage = container.querySelector(".about-member-stage");

    expect(stage).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pause team story/i })).toBeInTheDocument();

    fireEvent.pointerDown(stage!, { pointerId: 1, button: 0, clientX: 20, clientY: 20 });
    fireEvent.pointerUp(stage!, { pointerId: 1, button: 0, clientX: 20, clientY: 20 });
    expect(screen.getByRole("button", { name: /Play team story/i })).toBeInTheDocument();

    fireEvent.pointerDown(stage!, { pointerId: 2, button: 0, clientX: 20, clientY: 20 });
    fireEvent.pointerUp(stage!, { pointerId: 2, button: 0, clientX: 20, clientY: 20 });
    expect(screen.getByRole("button", { name: /Pause team story/i })).toBeInTheDocument();
  });

  it("uses one complete profile template with intentional media for all five members", () => {
    const { container } = render(<CommandChain />);
    const cards = Array.from(container.querySelectorAll<HTMLElement>(".about-teamCard"));

    expect(cards).toHaveLength(5);
    expect(container.querySelectorAll(".about-teamCard__media")).toHaveLength(5);
    expect(container.querySelectorAll(".about-teamCard__media > img")).toHaveLength(2);
    expect(container.querySelectorAll(".about-teamCard__portraitFallback")).toHaveLength(3);
    expect(container.querySelectorAll(".about-teamCard__connections")).toHaveLength(5);
    expect(container.querySelectorAll(".about-teamCard__footer")).toHaveLength(5);
    expect(container.querySelectorAll(".about-teamCard__linkGroup a.is-iconOnly")).toHaveLength(25);
    expect(screen.getAllByRole("link", { name: "acm@mcneese.edu", hidden: true })).toHaveLength(5);
    expect(screen.queryByText(/^Tenure$/i)).toBeNull();
    expect(screen.getAllByText("Contact")).toHaveLength(5);
    expect(screen.getAllByText("Social profiles")).toHaveLength(5);

    cards.filter((card) => card.dataset.storyState !== "active").forEach((card) => {
      card.querySelectorAll("a").forEach((link) => expect(link).toHaveAttribute("tabindex", "-1"));
    });
  });

  it("uses valid progress navigation and pauses for keyboard or wheel intent", () => {
    const { container } = render(<CommandChain />);
    const stage = container.querySelector(".about-member-stage");

    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByRole("navigation", { name: /Choose a team member/i })).toBeInTheDocument();

    fireEvent.focus(screen.getByRole("button", { name: /Next contributor/i }));
    expect(screen.getByRole("button", { name: /Play team story/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Play team story/i }));
    expect(screen.getByRole("button", { name: /Pause team story/i })).toBeInTheDocument();
    fireEvent.wheel(stage!);
    expect(screen.getByRole("button", { name: /Play team story/i })).toBeInTheDocument();
  });
});
