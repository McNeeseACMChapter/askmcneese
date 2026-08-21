import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentProps } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { UnifiedSidebar } from "./components/shell/UnifiedSidebar";
import type { Conversation } from "./types";

vi.mock("framer-motion", async () => {
  const actual = await vi.importActual<typeof import("framer-motion")>("framer-motion");
  return {
    ...actual,
    useReducedMotion: () => true,
  };
});

const conversations: Conversation[] = [
  {
    id: "c1",
    title: "hello",
    preview: "The reliable place for MLA format at McNeese State University library desk",
    updatedAt: new Date("2026-07-17T22:00:00Z"),
    messages: [],
  },
  {
    id: "c2",
    title: "Tuition deadlines for international students fall 2026",
    preview: "Priority registration windows",
    updatedAt: new Date("2026-07-16T22:00:00Z"),
    messages: [],
  },
];

function renderSidebar(
  overrides: Partial<ComponentProps<typeof UnifiedSidebar>> = {},
) {
  const props = {
    mode: "ask" as const,
    collapsed: false,
    onToggleCollapsed: vi.fn(),
    isMobile: false,
    mobileOpen: false,
    onMobileClose: vi.fn(),
    conversations,
    activeId: "c1",
    onSelectConversation: vi.fn(),
    onRename: vi.fn(),
    onTogglePin: vi.fn(),
    onDelete: vi.fn(),
    onNewChat: vi.fn(),
    ...overrides,
  };
  const view = render(
    <MemoryRouter initialEntries={["/ask"]}>
      <Routes>
        <Route path="/ask" element={<div>Ask route</div>} />
        <Route path="/about" element={<div>About route</div>} />
        <Route path="/settings" element={<div>Settings route</div>} />
        <Route path="/feedback" element={<div>Feedback route</div>} />
        <Route path="/acm/login" element={<div>ACM route</div>} />
      </Routes>
      <UnifiedSidebar {...props} />
    </MemoryRouter>,
  );
  return { ...view, props };
}

describe("premium desktop sidebar", () => {
  it("marks Ask as aria-current and keeps only one active primary route", () => {
    renderSidebar();
    const ask = screen.getByRole("link", { name: "Ask" });
    expect(ask).toHaveAttribute("aria-current", "page");
    expect(ask).toHaveClass("is-active");
    expect(screen.getByRole("link", { name: "About" })).not.toHaveAttribute(
      "aria-current",
      "page",
    );
    const actives = document.querySelectorAll(".appSidebarPrimaryNav .is-active");
    expect(actives).toHaveLength(1);
  });

  it("does not use a full gold active background", () => {
    renderSidebar();
    expect(document.querySelector(".liquid-drop-active")).toBeNull();
    const active = document.querySelector(".appSidebarNavItem.is-active") as HTMLElement;
    expect(active).toBeTruthy();
    const bg = getComputedStyle(active).backgroundColor;
    expect(bg).not.toMatch(/255,\s*206,\s*0/);
  });

  it("collapse control uses navigation labels and collapsed width token", async () => {
    const user = userEvent.setup();
    const onToggleCollapsed = vi.fn();
    const { rerender } = render(
      <MemoryRouter initialEntries={["/ask"]}>
        <UnifiedSidebar
          mode="ask"
          collapsed={false}
          onToggleCollapsed={onToggleCollapsed}
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

    const aside = screen.getByRole("complementary", { name: "AskMcNeese navigation" });
    expect(aside).toHaveClass("appSidebar");
    expect(aside.className).not.toContain("is-collapsed");
    expect(screen.getByRole("button", { name: "Collapse navigation" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );

    await user.click(screen.getByRole("button", { name: "Collapse navigation" }));
    expect(onToggleCollapsed).toHaveBeenCalled();

    rerender(
      <MemoryRouter initialEntries={["/ask"]}>
        <UnifiedSidebar
          mode="ask"
          collapsed
          onToggleCollapsed={onToggleCollapsed}
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

    const collapsed = screen.getByRole("complementary", { name: "AskMcNeese navigation" });
    expect(collapsed).toHaveClass("is-collapsed");
    expect(collapsed).toHaveAttribute("data-collapsed", "true");
    expect(screen.getByRole("button", { name: "Expand navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ask" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New conversation" })).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Search history")).not.toBeInTheDocument();
  });

  it("filters conversation history and preserves select + new chat behavior", async () => {
    const user = userEvent.setup();
    const { props } = renderSidebar();
    await user.type(screen.getByPlaceholderText("Search history"), "tuition");
    expect(screen.getByText(/Tuition deadlines/i)).toBeInTheDocument();
    expect(screen.queryByText("hello")).not.toBeInTheDocument();

    await user.clear(screen.getByPlaceholderText("Search history"));
    const tuitionRow = screen
      .getAllByRole("button")
      .find((button) => button.classList.contains("appSidebarHistoryButton") && /Tuition deadlines/i.test(button.textContent ?? ""));
    expect(tuitionRow).toBeTruthy();
    await user.click(tuitionRow!);
    expect(props.onSelectConversation).toHaveBeenCalledWith("c2");

    await user.click(screen.getByRole("button", { name: "New conversation" }));
    expect(props.onNewChat).toHaveBeenCalled();
  });

  it("preserves footer utility routes and truncates long titles", () => {
    renderSidebar();
    expect(screen.getByRole("link", { name: "Settings" })).toHaveAttribute("href", "/settings");
    expect(screen.getByRole("link", { name: "Feedback" })).toHaveAttribute("href", "/feedback");
    expect(screen.queryByRole("link", { name: "ACM portal" })).toBeNull();
    const longTitle = screen.getByText(/Tuition deadlines/i);
    expect(longTitle).toHaveClass("appSidebarHistoryTitle");
  });

  it("keeps header/footer outside the scrolling history list", () => {
    renderSidebar();
    const aside = screen.getByRole("complementary", { name: "AskMcNeese navigation" });
    expect(aside.querySelector(".appSidebarHeader")).toBeTruthy();
    expect(aside.querySelector(".appSidebarPrimaryNav")).toBeTruthy();
    expect(aside.querySelector(".appSidebarUtilities")).toBeTruthy();
    const history = aside.querySelector(".appSidebarHistory") as HTMLElement;
    expect(history).toBeTruthy();
    expect(history.className).toContain("appSidebarHistory");
    expect(aside.querySelector(".appSidebarHeader")?.compareDocumentPosition(history) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(history.compareDocumentPosition(aside.querySelector(".appSidebarUtilities")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(history).queryByRole("link", { name: "Ask" })).toBeNull();
  });

  it("disables collapse transition under reduced motion", () => {
    renderSidebar({ collapsed: false });
    const aside = screen.getByRole("complementary", { name: "AskMcNeese navigation" });
    expect(aside).toHaveAttribute("data-reduced-motion", "true");
    expect(aside).toHaveStyle({ transition: "none" });
  });
});
