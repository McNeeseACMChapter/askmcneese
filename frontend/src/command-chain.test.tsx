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
    expect(tabs.filter((tab) => tab.getAttribute("aria-selected") === "true")).toHaveLength(1);

    const evanTab = screen.getByRole("tab", { name: /Evan Weber/i });
    fireEvent.click(evanTab);
    expect(evanTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel", { name: /Evan Weber/i })).toHaveTextContent(/Product experience/i);

    fireEvent.keyDown(evanTab, { key: "ArrowDown" });
    expect(screen.getByRole("tab", { name: /Dr\. Vipin Menon/i })).toHaveAttribute("aria-selected", "true");
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

  it("starts autoplay and lets the story surface pause and resume it", () => {
    const { container } = render(<CommandChain />);
    const stage = container.querySelector(".about-member-stage");

    expect(stage).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pause team story/i })).toBeInTheDocument();

    fireEvent.click(stage!);
    expect(screen.getByRole("button", { name: /Play team story/i })).toBeInTheDocument();

    fireEvent.click(stage!);
    expect(screen.getByRole("button", { name: /Pause team story/i })).toBeInTheDocument();
  });
});