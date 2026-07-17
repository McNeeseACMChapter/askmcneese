import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { UnifiedSidebar } from "./components/shell/UnifiedSidebar";
import { LiveAnswerProgress } from "./components/chat/LiveAnswerProgress";
import { EmptyState } from "./components/chat/EmptyState";
import { CitationGroup } from "./components/chat/CitationGroup";
import { ChatInput } from "./components/chat/ChatInput";
import { ChatPage } from "./components/chat/ChatPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { AcmLoginPage } from "./pages/AcmLoginPage";
import { applyActivityEvent, completeAskRun, createAskRun } from "./lib/askRun";

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
      article: passthrough("article"),
      button: passthrough("button"),
      ul: passthrough("ul"),
      ol: passthrough("ol"),
      li: passthrough("li"),
      section: passthrough("section"),
      a: passthrough("a"),
      span: passthrough("span"),
      svg: passthrough("svg"),
    },
    AnimatePresence: ({ children }: React.PropsWithChildren) => children,
    useReducedMotion: () => false,
  };
});

describe("unified navigation", () => {
  it("renders text-first desktop nav with ACM Portal", () => {
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
    expect(screen.getByRole("link", { name: "AskMcNeese" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ask" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "ACM Portal" })).toHaveAttribute("href", "/acm/login");
  });

  it("top collapse icon toggles and collapsed rail exposes expand", async () => {
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

    const aside = screen.getByRole("complementary", { name: "Application" });
    expect(aside).toHaveAttribute("data-collapsed", "false");
    expect(aside.className).not.toContain("is-collapsed");

    await user.click(screen.getByRole("button", { name: /Collapse sidebar/i }));
    expect(onToggleCollapsed).toHaveBeenCalledTimes(1);

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

    const collapsedAside = screen.getByRole("complementary", { name: "Application" });
    expect(collapsedAside).toHaveAttribute("data-collapsed", "true");
    expect(collapsedAside.className).toContain("is-collapsed");
    await user.click(screen.getByRole("button", { name: /Expand sidebar/i }));
    expect(onToggleCollapsed).toHaveBeenCalledTimes(2);
  });
});

describe("LiveAnswerProgress compact", () => {
  function buildRun() {
    let run = createAskRun({
      runId: "run-1",
      requestId: "r1",
      turnId: "t1",
      userMessageId: "u1",
      assistantMessageId: "a1",
    });
    for (const item of [
      { event: "request.accepted", message: "Got your question — starting now", elapsedMs: 120 },
      {
        event: "retrieval.completed",
        message: "Finished collecting sources",
        elapsedMs: 800,
        metadata: { sources_found: 3 },
      },
      { event: "answer.generating", message: "Writing your answer from those sources", elapsedMs: 1200 },
    ] as const) {
      run = applyActivityEvent(run, { requestId: "r1", ...item });
    }
    return run;
  }

  it("is compact by default while active with live header", () => {
    render(<LiveAnswerProgress run={{ ...buildRun(), status: "streaming" }} />);
    expect(screen.getByText("Live")).toBeInTheDocument();
    expect(screen.getAllByText(/Writing your answer from those sources/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Stop/i)).not.toBeInTheDocument();
    expect(document.querySelector(".live-progress-dot")).toBeNull();
    expect(document.querySelector(".live-activity-icon")).toBeNull();
  });

  it("shows compact completion summary by default", () => {
    const completed = completeAskRun(buildRun(), "completed");
    render(<LiveAnswerProgress run={completed} />);
    expect(screen.getByText(/Campus live|Knowledge|Answer prepared|Answer ready|Search interrupted/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /View activity/i })).toBeInTheDocument();
  });
});

describe("sources disclosure", () => {
  it("uses Sources · N without Official sources heading", async () => {
    const user = userEvent.setup();
    render(
      <CitationGroup
        citations={[
          { id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" },
          { id: "2", title: "Calendar", url: "https://www.mcneese.edu/calendar" },
        ]}
      />,
    );
    expect(screen.getByRole("button", { name: /Sources · 2/i })).toBeInTheDocument();
    expect(screen.queryByText(/Official sources/i)).not.toBeInTheDocument();
    // 1–2 sources expand by default; clicking collapses.
    expect(screen.getByText("Admissions")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Sources · 2/i }));
    await waitFor(() => {
      expect(screen.queryByText("Admissions")).not.toBeInTheDocument();
    });
  });
});

describe("composer dock layout", () => {
  it("docks the input pill outside the thread scroller with shrink-0", () => {
    const { container } = render(
      <MemoryRouter>
        <ChatPage
          messages={[]}
          isLoading={false}
          askStatus="idle"
          activeRun={null}
          offline={false}
          sourceScope="knowledge"
          onSend={() => undefined}
          onStop={() => undefined}
          onSourceScopeChange={() => undefined}
        />
      </MemoryRouter>,
    );
    const column = container.querySelector(".chatColumn");
    const thread = container.querySelector(".chatThread");
    const dock = container.querySelector(".composerDock");
    expect(column).toBeTruthy();
    expect(thread).toBeTruthy();
    expect(dock).toBeTruthy();
    expect(dock?.className).toContain("shrink-0");
    expect(thread?.contains(dock as Node)).toBe(false);
    expect(screen.getByRole("textbox", { name: /AskMcNeese question/i })).toBeVisible();
    expect(screen.getByRole("heading", { name: "AskMcNeese" })).toBeVisible();
    expect(screen.getByText(/Optional places to start/i)).toBeVisible();
  });

  it("shows trust caution and a single Send control", () => {
    render(
      <MemoryRouter>
        <ChatInput
          onSend={() => undefined}
          onStop={() => undefined}
          loading={false}
          offline={false}
          state="idle"
          sourceScope="knowledge"
          onSourceScopeChange={() => undefined}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText(/AskMcNeese can make mistakes/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Send question/i })).toBeInTheDocument();
    expect(screen.getByText(/Press Enter to send/i).className).toContain("sr-only");
  });
});

describe("branding", () => {
  it("empty state has no invented brand icon or duplicate methodology links", () => {
    render(
      <MemoryRouter>
        <EmptyState onSuggestionClick={() => undefined} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "AskMcNeese" })).toBeInTheDocument();
    expect(document.querySelector("svg.lucide-library")).toBeNull();
    expect(document.querySelector("svg.lucide-sparkles")).toBeNull();
    expect(screen.getAllByRole("link", { name: /About the team and what AskMcNeese does/i })).toHaveLength(1);
  });
});

describe("ACM Portal", () => {
  it("renders member login intro and verification form", () => {
    render(
      <MemoryRouter>
        <AcmLoginPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /ACM Member Login/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Verify & log in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/McNeese email/i)).toBeInTheDocument();
  });

  it("acknowledges submit without authenticating", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/acm/login"]}>
        <Routes>
          <Route path="/acm/login" element={<AcmLoginPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await user.type(screen.getByLabelText(/McNeese email/i), "member@mcneese.edu");
    await user.type(screen.getByLabelText(/ACM member ID/i), "ACM-001");
    await user.type(screen.getByLabelText(/^Password$/i), "secret");
    await user.click(screen.getByRole("button", { name: /Verify & log in/i }));
    expect(screen.getByRole("status")).toHaveTextContent(/not connected yet/i);
  });
});

describe("404", () => {
  it("renders polished not found", () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: /Return to Ask/i })).toBeInTheDocument();
  });
});
