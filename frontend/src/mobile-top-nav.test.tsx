import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { MobileTopNavigation } from "./components/shell/MobileNavigation";

vi.mock("framer-motion", async () => {
  const React = await import("react");
  const passthrough =
    (tag: string) =>
    ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) =>
      React.createElement(tag, props, children);
  return {
    motion: {
      nav: passthrough("nav"),
      div: passthrough("div"),
      span: passthrough("span"),
      button: passthrough("button"),
    },
    AnimatePresence: ({ children }: React.PropsWithChildren) => children,
    useReducedMotion: () => true,
  };
});

function renderNav(path: string, onOpenHistory = vi.fn()) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="*" element={<MobileTopNavigation onOpenHistory={onOpenHistory} />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("MobileTopNavigation", () => {
  it("marks Ask as the current page on /ask", () => {
    renderNav("/ask");
    expect(screen.getByRole("navigation", { name: "Primary mobile navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute("data-active", "true");
    expect(screen.getByRole("link", { name: "About" })).not.toHaveAttribute("aria-current");
  });

  it("marks About current on nested about routes", () => {
    renderNav("/about");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("data-active", "true");
  });

  it("keeps Updates and Status out of the primary capsule", () => {
    renderNav("/ask");
    expect(screen.queryByRole("link", { name: "Updates" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Status" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "History" })).toBeInTheDocument();
  });

  it("opens History from the primary capsule", async () => {
    const user = userEvent.setup();
    const onOpenHistory = vi.fn();
    renderNav("/ask", onOpenHistory);
    await user.click(screen.getByRole("button", { name: "History" }));
    expect(onOpenHistory).toHaveBeenCalledOnce();
  });

  it("puts Updates in More and does not duplicate Methodology", async () => {
    const user = userEvent.setup();
    renderNav("/ask");
    await user.click(screen.getByRole("button", { name: "More" }));
    expect(screen.getByRole("dialog", { name: "More" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Updates" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Status" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Methodology" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Roadmap" })).not.toBeInTheDocument();
  });

  it("does not render a bottom-fixed mobile primary bar", () => {
    renderNav("/ask");
    expect(screen.queryByRole("navigation", { name: "Mobile primary" })).not.toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "Primary mobile navigation" });
    expect(nav.className).toContain("mobile-top-nav");
  });
});
