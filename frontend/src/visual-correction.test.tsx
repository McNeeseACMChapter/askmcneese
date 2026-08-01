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
    expect(screen.getByRole("link", { name: "ACM portal" })).toHaveAttribute("href", "/acm/login");
    expect(document.querySelector(".liquid-drop-active")).toBeNull();
    expect(document.querySelector(".appSidebarNavItem.is-active")).toBeTruthy();
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

    const aside = screen.getByRole("complementary", { name: "AskMcNeese navigation" });
    expect(aside).toHaveAttribute("data-collapsed", "false");
    expect(aside.className).not.toContain("is-collapsed");

    await user.click(screen.getByRole("button", { name: /Collapse navigation/i }));
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

    const collapsedAside = screen.getByRole("complementary", { name: "AskMcNeese navigation" });
    expect(collapsedAside).toHaveAttribute("data-collapsed", "true");
    expect(collapsedAside.className).toContain("is-collapsed");
    await user.click(screen.getByRole("button", { name: /Expand navigation/i }));
    expect(onToggleCollapsed).toHaveBeenCalledTimes(2);
  });
});

describe("LiveAnswerProgress trail", () => {
  function buildRun() {
    let run = createAskRun({
      runId: "run-1",
      requestId: "r1",
      turnId: "t1",
      userMessageId: "u1",
      assistantMessageId: "a1",
    });
    for (const item of [
      {
        event: "request.accepted",
        message: "Starting your request",
        elapsedMs: 120,
        metadata: { phase: "understand", kind: "milestone" },
      },
      {
        event: "retrieval.completed",
        message: "Collected the relevant sources",
        elapsedMs: 800,
        metadata: { sources_found: 3, phase: "search", kind: "milestone" },
      },
      {
        event: "answer.generating",
        message: "Writing your answer",
        elapsedMs: 1200,
        metadata: { phase: "compose", kind: "milestone" },
      },
    ] as const) {
      run = applyActivityEvent(run, { requestId: "r1", runId: "run-1", ...item });
    }
    return run;
  }

  it("shows borderless compact write narration while streaming", () => {
    render(<LiveAnswerProgress run={{ ...buildRun(), status: "streaming" }} />);
    expect(screen.getAllByText(/Writing your answer/i).length).toBeGreaterThan(0);
    expect(document.querySelector(".researchTrail")).toBeTruthy();
    expect(document.querySelector(".liveTrailRail")).toBeNull();
    expect(document.querySelector(".liveTrail")).toBeNull();
    expect(screen.queryByText(/^Understand$/)).toBeNull();
  });

  it("shows compact completion summary by default", () => {
    const completed = completeAskRun(buildRun(), "completed");
    render(<LiveAnswerProgress run={completed} />);
    expect(screen.getByText(/Research complete/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /View activity/i })).toBeInTheDocument();
  });
});

describe("sources disclosure", () => {
  it("uses Sources · N without Official sources heading and stays collapsed", async () => {
    const user = userEvent.setup();
    render(
      <CitationGroup
        citations={[
          { id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" },
          { id: "2", title: "Calendar", url: "https://www.mcneese.edu/calendar" },
        ]}
      />,
    );
    expect(screen.getByRole("button", { name: /Sources/i })).toBeInTheDocument();
    expect(screen.queryByText(/Official sources/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Admissions")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Sources/i }));
    await waitFor(() => {
      expect(screen.getByText("Admissions")).toBeInTheDocument();
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
          requestVisualState={{ requestId: 0, phase: "idle" }}
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
    expect(screen.getByRole("heading", { name: /What are you trying to figure out/i })).toBeVisible();
    expect(screen.queryByText(/Optional places to start/i)).toBeNull();
  });

  it("shows a single Send control without permanent caution under the composer", () => {
    render(
      <ChatInput
        onSend={() => undefined}
        onStop={() => undefined}
        loading={false}
        offline={false}
        state="idle"
        sourceScope="knowledge"
        onSourceScopeChange={() => undefined}
      />,
    );
    expect(screen.queryByText(/AskMcNeese can make mistakes/i)).toBeNull();
    expect(screen.getByRole("button", { name: /Send question/i })).toBeInTheDocument();
    expect(screen.getByText(/Press Enter to send/i).className).toContain("sr-only");
  });
});

describe("branding", () => {
  it("presents a campus-first welcome with source responsibility and editorial starting paths", () => {
    render(
      <MemoryRouter>
        <EmptyState />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /What are you trying to figure out/i })).toBeInTheDocument();
    expect(screen.getByText(/A guide, not the final authority/i)).toBeInTheDocument();
    expect(document.querySelector("svg.lucide-library")).toBeNull();
    expect(document.querySelector("svg.lucide-sparkles")).toBeNull();
    expect(screen.queryByText(/Optional places to start/i)).toBeNull();
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
    expect(screen.getByLabelText(/^Email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Email$/i)).toHaveValue("admin");
    expect(screen.getByLabelText(/ACM member ID/i)).toHaveValue("123");
  });

  it("rejects wrong credentials and accepts demo admin login", async () => {
    const user = userEvent.setup();
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });

    render(
      <MemoryRouter initialEntries={["/acm/login"]}>
        <Routes>
          <Route path="/acm/login" element={<AcmLoginPage />} />
        </Routes>
      </MemoryRouter>,
    );
    const email = screen.getByLabelText(/^Email$/i);
    const memberId = screen.getByLabelText(/ACM member ID/i);
    const password = screen.getByLabelText(/^Password$/i);
    await user.clear(email);
    await user.clear(memberId);
    await user.clear(password);
    await user.type(email, "wrong@mcneese.edu");
    await user.type(memberId, "999");
    await user.type(password, "nope");
    await user.click(screen.getByRole("button", { name: /Verify & log in/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/do not match/i);
    expect(assign).not.toHaveBeenCalled();

    await user.clear(email);
    await user.clear(memberId);
    await user.clear(password);
    await user.type(email, "admin");
    await user.type(memberId, "123");
    await user.type(password, "pass123");
    await user.click(screen.getByRole("button", { name: /Verify & log in/i }));
    expect(assign).toHaveBeenCalledWith("http://127.0.0.1:3100/home");
    vi.unstubAllGlobals();
  }, 10_000);
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
