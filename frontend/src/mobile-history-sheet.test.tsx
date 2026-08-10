import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MobileHistorySheet } from "./components/shell/MobileHistorySheet";
import type { Conversation } from "./types";

vi.mock("framer-motion", async () => {
  const React = await import("react");
  const passthrough = (tag: string) =>
    React.forwardRef<HTMLElement, React.PropsWithChildren<Record<string, unknown>>>(
      ({ children, ...props }, ref) => {
        const {
          initial: _initial,
          animate: _animate,
          exit: _exit,
          transition: _transition,
          ...domProps
        } = props;
        return React.createElement(tag, { ...domProps, ref }, children);
      },
    );
  return {
    motion: { div: passthrough("div") },
    AnimatePresence: ({ children }: React.PropsWithChildren) => children,
    useReducedMotion: () => true,
  };
});

const conversations: Conversation[] = [
  {
    id: "conversation-1",
    title: "Summer registration",
    preview: "When does registration close?",
    updatedAt: new Date("2026-08-01T12:00:00Z"),
    messages: [],
  },
  {
    id: "conversation-2",
    title: "Degree plan",
    preview: "Mechanical engineering courses",
    updatedAt: new Date("2026-08-02T12:00:00Z"),
    messages: [],
  },
];

function renderHistory(overrides: Partial<React.ComponentProps<typeof MobileHistorySheet>> = {}) {
  const props = {
    open: true,
    conversations,
    activeId: "conversation-1",
    onClose: vi.fn(),
    onSelectConversation: vi.fn(),
    onNewChat: vi.fn(),
    onRename: vi.fn(),
    onDelete: vi.fn(),
    ...overrides,
  };
  render(<MobileHistorySheet {...props} />);
  return props;
}

describe("MobileHistorySheet", () => {
  it("renames a conversation through the explicit action rail", () => {
    const props = renderHistory();

    fireEvent.click(screen.getByRole("button", { name: "Options for Summer registration" }));
    expect(screen.getByRole("button", { name: "Options for Summer registration" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    fireEvent.click(screen.getByRole("button", { name: "Rename Summer registration" }));

    const input = screen.getByRole("textbox", { name: "Conversation title" });
    fireEvent.change(input, { target: { value: "Fall registration" } });
    fireEvent.click(screen.getByRole("button", { name: "Save conversation title" }));

    expect(props.onRename).toHaveBeenCalledWith("conversation-1", "Fall registration");
  });

  it("requires confirmation before deleting", () => {
    const props = renderHistory();

    fireEvent.click(screen.getByRole("button", { name: "Options for Degree plan" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete Degree plan" }));

    const confirmation = screen.getByRole("alertdialog", { name: "Delete conversation?" });
    expect(within(confirmation).getByText(/Degree plan/)).toBeInTheDocument();
    expect(props.onDelete).not.toHaveBeenCalled();

    fireEvent.click(within(confirmation).getByRole("button", { name: "Keep it" }));
    expect(props.onDelete).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Options for Degree plan" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete Degree plan" }));
    fireEvent.click(screen.getByRole("alertdialog").getElementsByTagName("button")[1]);

    expect(props.onDelete).toHaveBeenCalledWith("conversation-2");
  });

  it("reveals actions with a leftward touch swipe without selecting the conversation", () => {
    const props = renderHistory();
    const row = screen.getByRole("button", { name: "Options for Summer registration" }).closest("li");
    const surface = row?.querySelector<HTMLElement>(".mobile-historyItemSurface");
    expect(surface).not.toBeNull();

    fireEvent.pointerDown(surface!, { pointerId: 1, pointerType: "touch", clientX: 260, clientY: 120 });
    fireEvent.pointerMove(surface!, { pointerId: 1, pointerType: "touch", clientX: 150, clientY: 123 });
    fireEvent.pointerUp(surface!, { pointerId: 1, pointerType: "touch", clientX: 150, clientY: 123 });

    expect(row).toHaveAttribute("data-revealed", "true");
    expect(props.onSelectConversation).not.toHaveBeenCalled();
  });
});
