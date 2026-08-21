import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PublicAppShell } from "./components/shell/PublicAppShell";

vi.mock("./components/shell/MobileNavigation", () => ({
  MobileTopNavigation: () => <nav aria-label="Primary mobile navigation" />,
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
      span: passthrough("span"),
      nav: passthrough("nav"),
      button: passthrough("button"),
    },
    AnimatePresence: ({ children }: React.PropsWithChildren) => children,
    useReducedMotion: () => true,
  };
});

function mockMatchMedia(matchesFor: (query: string) => boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: matchesFor(query),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

const shellProps = {
  healthStatus: "online" as const,
  sidebarCollapsed: false,
  onToggleSidebarCollapsed: () => undefined,
  setSidebarCollapsed: () => undefined,
  mobileNavOpen: false,
  onMobileNavOpenChange: () => undefined,
  conversations: [],
  activeId: null,
  onSelectConversation: () => undefined,
  onRename: () => undefined,
  onTogglePin: () => undefined,
  onDelete: () => undefined,
  onNewChat: () => undefined,
};

describe("public shell route header", () => {
  beforeEach(() => {
    mockMatchMedia((query) => {
      if (query.includes("min-width: 1024")) return true;
      if (query.includes("min-width: 768")) return true;
      return false;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not mount route-header on desktop Ask (empty or titled)", () => {
    const { rerender } = render(
      <MemoryRouter initialEntries={["/ask"]}>
        <Routes>
          <Route
            element={
              <PublicAppShell {...shellProps} desktop routeLabel="AskMcNeese" />
            }
          >
            <Route path="/ask" element={<div>Ask canvas</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(document.querySelector(".route-header")).toBeNull();
    expect(document.querySelector(".public-shell--ask-desktop")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Open navigation/i })).toBeNull();

    rerender(
      <MemoryRouter initialEntries={["/ask"]}>
        <Routes>
          <Route
            element={
              <PublicAppShell {...shellProps} desktop routeLabel="MLA formatting help" />
            }
          >
            <Route path="/ask" element={<div>Ask canvas</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(document.querySelector(".route-header")).toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: "MLA formatting help" })).toHaveClass(
      "sr-only",
    );
  });

  it("keeps contextual header on desktop non-Ask routes", () => {
    render(
      <MemoryRouter initialEntries={["/about"]}>
        <Routes>
          <Route
            element={<PublicAppShell {...shellProps} desktop routeLabel="About" />}
          >
            <Route path="/about" element={<div>About page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    const header = document.querySelector(".route-header--contextual");
    expect(header).toBeTruthy();
    expect(header?.textContent).toContain("About");
  });

  it("keeps compact tablet header with menu on Ask when not desktop", () => {
    mockMatchMedia((query) => {
      if (query.includes("min-width: 1024")) return false;
      if (query.includes("min-width: 768")) return true;
      return false;
    });

    render(
      <MemoryRouter initialEntries={["/ask"]}>
        <Routes>
          <Route
            element={
              <PublicAppShell {...shellProps} desktop={false} routeLabel="AskMcNeese" />
            }
          >
            <Route path="/ask" element={<div>Ask canvas</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(document.querySelector(".route-header--tablet")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Open navigation/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /ACM/i })).toBeNull();
  });
});
