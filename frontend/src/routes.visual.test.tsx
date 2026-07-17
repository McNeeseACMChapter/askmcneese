import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { UnifiedSidebar } from "./components/shell/UnifiedSidebar";
import { AboutOverview } from "./pages/about/AboutOverview";

vi.mock("@gsap/react", () => ({
  useGSAP: () => undefined,
}));

vi.mock("./lib/gsap", () => ({
  ensureGsap: () => ({
    gsap: { fromTo: vi.fn(), matchMedia: () => ({ add: vi.fn(), revert: vi.fn() }) },
    ScrollTrigger: { create: vi.fn(), getAll: () => [], refresh: vi.fn() },
  }),
  prefersReducedMotion: () => true,
  isDesktopScrollStory: () => false,
}));

vi.mock("framer-motion", async () => {
  const React = await import("react");
  const passthrough =
    (tag: string) =>
    ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) =>
      React.createElement(tag, props, children);
  return {
    motion: {
      div: passthrough("div"),
      p: passthrough("p"),
      span: passthrough("span"),
      h1: passthrough("h1"),
      article: passthrough("article"),
      button: passthrough("button"),
      ul: passthrough("ul"),
      li: passthrough("li"),
      section: passthrough("section"),
      a: passthrough("a"),
    },
    AnimatePresence: ({ children }: React.PropsWithChildren) => children,
    useReducedMotion: () => true,
  };
});

describe("public routes", () => {
  it("marks Ask as current in unified sidebar", () => {
    render(
      <MemoryRouter initialEntries={["/ask"]}>
        <UnifiedSidebar
          mode="ask"
          collapsed={false}
          onToggleCollapsed={() => undefined}
          isMobile={false}
          mobileOpen={false}
          onMobileClose={() => undefined}
          conversations={[]}
          activeId={null}
          onSelectConversation={() => undefined}
          onRename={() => undefined}
          onTogglePin={() => undefined}
          onDelete={() => undefined}
          onNewChat={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute("aria-current", "page");
  });

  it("marks About as current on about route", () => {
    render(
      <MemoryRouter initialEntries={["/about"]}>
        <UnifiedSidebar
          mode="about"
          collapsed={false}
          onToggleCollapsed={() => undefined}
          isMobile={false}
          mobileOpen={false}
          onMobileClose={() => undefined}
          conversations={[]}
          activeId={null}
          onSelectConversation={() => undefined}
          onRename={() => undefined}
          onTogglePin={() => undefined}
          onDelete={() => undefined}
          onNewChat={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("aria-current", "page");
  });

  it("renders About page with team and purpose", () => {
    render(
      <MemoryRouter>
        <AboutOverview />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /Who steers AskMcNeese/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /What AskMcNeese does/i })).toBeInTheDocument();
  });

  it("supports navigation between routes", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/about"]}>
        <Routes>
          <Route path="/ask" element={<div>Ask route</div>} />
          <Route path="/about" element={<div>About route</div>} />
        </Routes>
        <UnifiedSidebar
          mode="about"
          collapsed={false}
          onToggleCollapsed={() => undefined}
          isMobile={false}
          mobileOpen={false}
          onMobileClose={() => undefined}
          conversations={[]}
          activeId={null}
          onSelectConversation={() => undefined}
          onRename={() => undefined}
          onTogglePin={() => undefined}
          onDelete={() => undefined}
          onNewChat={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("About route")).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Ask" }));
    expect(screen.getByText("Ask route")).toBeInTheDocument();
  });
});
