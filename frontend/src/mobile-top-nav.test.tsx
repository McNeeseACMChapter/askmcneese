import { render, screen, within } from "@testing-library/react";
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
    expect(screen.getByRole("link", { name: "About" })).toBeInTheDocument();
  });

  it("keeps About direct and History out of the primary header", () => {
    renderNav("/ask");
    expect(screen.getByRole("link", { name: "About" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "History" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Menu" })).toBeInTheDocument();
  });

  it("opens History from the hamburger menu", async () => {
    const user = userEvent.setup();
    const onOpenHistory = vi.fn();
    renderNav("/ask", onOpenHistory);
    await user.click(screen.getByRole("button", { name: "Menu" }));
    expect(screen.getByRole("dialog", { name: "Menu" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "History" }));
    expect(onOpenHistory).toHaveBeenCalledOnce();
  });

  it("uses one quiet menu title and restores focus when dismissed", async () => {
    const user = userEvent.setup();
    renderNav("/ask");
    const trigger = screen.getByRole("button", { name: "Menu" });

    await user.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "Menu" });
    expect(within(dialog).getByRole("heading", { name: "Menu" })).toBeInTheDocument();
    expect(within(dialog).queryByText("AskMcNeese")).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "History" })).toHaveClass("mobile-moreLink");
    expect(screen.getByRole("button", { name: "Close menu" })).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "Menu" })).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("puts Class Planner, Updates, and Usage in the menu without duplicating About", async () => {
    const user = userEvent.setup();
    renderNav("/ask");
    await user.click(screen.getByRole("button", { name: "Menu" }));
    expect(screen.getByRole("link", { name: "Class Planner" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "About" })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Updates" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Usage" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Status" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /ACM/i })).not.toBeInTheDocument();
  });

  it("makes the current destination unmistakable inside the menu", async () => {
    const user = userEvent.setup();
    renderNav("/settings");
    await user.click(screen.getByRole("button", { name: "Menu" }));

    const settings = screen.getByRole("link", { name: "Settings" });
    expect(settings).toHaveAttribute("aria-current", "page");
    expect(settings).toHaveClass("mobile-more-link-active");
    expect(screen.getByRole("region", { name: "Main" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Support" })).toBeInTheDocument();
  });

  it("does not render a bottom-fixed mobile primary bar", () => {
    renderNav("/ask");
    expect(screen.queryByRole("navigation", { name: "Mobile primary" })).not.toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "Primary mobile navigation" });
    expect(nav.className).toContain("mobile-top-nav");
  });
});
