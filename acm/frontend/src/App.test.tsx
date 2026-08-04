import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import { isNavVisible } from "./components/shell/AcmSidebar";
import { ToastProvider } from "./components/toast/ToastProvider";
import { PrototypeProvider } from "./state/PrototypeContext";

afterEach(() => {
  cleanup();
});

function renderAt(path: string) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <PrototypeProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </PrototypeProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ACM Panel corrective foundation", () => {
  it("marks Home as the active navigation destination", () => {
    renderAt("/home");
    const nav = screen.getByLabelText("ACM Panel navigation");
    const home = within(nav).getByRole("link", { name: /^home$/i });
    expect(home).toHaveAttribute("aria-current", "page");
  });

  it("collapses the sidebar", async () => {
    const user = userEvent.setup();
    renderAt("/home");
    const nav = screen.getByLabelText("ACM Panel navigation");
    await user.click(within(nav).getByRole("button", { name: "Collapse navigation" }));
    expect(nav).toHaveAttribute("data-collapsed", "true");
  });

  it("opens the mobile More sheet", async () => {
    const user = userEvent.setup();
    renderAt("/home");
    const mobile = screen.getByLabelText("Primary mobile navigation");
    await user.click(within(mobile).getByRole("button", { name: /^more$/i }));
    expect(screen.getByRole("dialog", { name: /more navigation/i })).toBeInTheDocument();
  });

  it("gates Administration by fixture permissions", () => {
    expect(isNavVisible(false, false, { requiredPermission: "admin" })).toBe(false);
    expect(isNavVisible(true, false, { requiredPermission: "admin" })).toBe(true);
  });

  it("renders Home as a prioritized chapter briefing", () => {
    renderAt("/home");
    expect(screen.getByText("Projects at risk")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /needs your attention/i })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: /active project portfolio/i })).toBeInTheDocument();
  });

  it("maps editability and persistence boundaries across modules", () => {
    renderAt("/data-access");
    expect(screen.getByRole("heading", { name: /module editability map/i })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: /module data access contract/i })).toBeInTheDocument();
    expect(screen.getByText("Append-only audit log")).toBeInTheDocument();
  });

  it("opens a bounded managed editor for the assigned project", async () => {
    const user = userEvent.setup();
    renderAt("/projects/proj-ask-2");
    await user.click(screen.getByRole("button", { name: /edit project/i }));
    const dialog = screen.getByRole("dialog", { name: /edit managed project fields/i });
    expect(within(dialog).getByText("Workflow-controlled")).toBeInTheDocument();
    expect(within(dialog).getByText("Calculated")).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: /save durable record/i })).toBeDisabled();
  });
  it("renders Meetings as a meaningful workspace", () => {
    renderAt("/meetings");
    expect(screen.getByRole("heading", { level: 1, name: /meetings/i })).toBeInTheDocument();
    expect(screen.queryByText(/reserved for a later pass/i)).toBeNull();
  });

  it("renders Reports analytics workspace", () => {
    renderAt("/reports");
    expect(screen.getByRole("heading", { level: 1, name: /reports/i })).toBeInTheDocument();
    expect(screen.queryByText(/reserved for a later pass/i)).toBeNull();
  });

  it("exposes projects collection views", () => {
    renderAt("/projects");
    expect(screen.getByRole("heading", { level: 1, name: /projects/i })).toBeInTheDocument();
  });
});
