import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CommandChain } from "./components/about/CommandChain";

vi.mock("framer-motion", async () => {
  const React = await import("react");
  const passthrough =
    (tag: string) =>
    ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) =>
      React.createElement(tag, props, children);
  return {
    motion: {
      div: passthrough("div"),
      article: passthrough("article"),
    },
    useReducedMotion: () => true,
  };
});

describe("CommandChain", () => {
  it("renders ACM → advisor → PM → builders hierarchy", () => {
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

  it("marks Landon as former in the tenure badge", () => {
    render(<CommandChain />);
    expect(screen.getAllByText(/Former · June 8 – July 2/i).length).toBeGreaterThan(0);
  });

  it("shows a days-in-role counter beside tenure badges", () => {
    render(<CommandChain />);
    expect(screen.getAllByTitle("Days in this role").length).toBeGreaterThanOrEqual(5);
  });
});
