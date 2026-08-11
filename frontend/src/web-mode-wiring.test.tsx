import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInput } from "./components/chat/ChatInput";
import type { ComposerState, SourceScope } from "./types";

type ChatInputTestProps = {
  onSend: (text: string) => void;
  onStop: () => void;
  loading: boolean;
  offline: boolean;
  state: ComposerState;
  sourceScope: SourceScope;
  onSourceScopeChange: (scope: SourceScope) => void;
  webSearchAvailable?: boolean;
};

function renderChatInput(props: ChatInputTestProps) {
  return render(<ChatInput {...props} />);
}

describe("ChatInput source scope", () => {
  it("selects adaptive, knowledge, and web and keeps canonical values", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const { rerender } = renderChatInput({
      onSend: vi.fn(),
      onStop: vi.fn(),
      loading: false,
      offline: false,
      state: "idle",
      sourceScope: "adaptive",
      onSourceScopeChange: onChange,
      webSearchAvailable: true,
    });

    const trigger = screen.getByRole("button", { name: "Choose source mode" });
    expect(trigger).toHaveAttribute("data-value", "adaptive");
    await user.click(trigger);
    await user.click(screen.getByRole("option", { name: /Include the web/i }));
    expect(onChange).toHaveBeenCalledWith("web");

    rerender(
      <ChatInput
        onSend={vi.fn()}
        onStop={vi.fn()}
        loading={false}
        offline={false}
        state="idle"
        sourceScope="web"
        onSourceScopeChange={onChange}
        webSearchAvailable
      />,
    );
    expect(
      screen.getByRole("button", { name: "Choose source mode" }),
    ).toHaveAttribute("data-value", "web");
  });

  it("disables source mode when live web is unavailable", () => {
    const onChange = vi.fn();
    renderChatInput({
      onSend: vi.fn(),
      onStop: vi.fn(),
      loading: false,
      offline: false,
      state: "idle",
      sourceScope: "knowledge",
      onSourceScopeChange: onChange,
      webSearchAvailable: false,
    });
    expect(screen.getByLabelText("Choose source mode")).toBeDisabled();
    expect(screen.getAllByText(/McNeese only/).length).toBeGreaterThan(0);
  });

  it("resets to knowledge when web becomes unavailable", () => {
    const onChange = vi.fn();
    const { rerender } = renderChatInput({
      onSend: vi.fn(),
      onStop: vi.fn(),
      loading: false,
      offline: false,
      state: "idle",
      sourceScope: "adaptive",
      onSourceScopeChange: onChange,
      webSearchAvailable: true,
    });
    rerender(
      <ChatInput
        onSend={vi.fn()}
        onStop={vi.fn()}
        loading={false}
        offline={false}
        state="idle"
        sourceScope="adaptive"
        onSourceScopeChange={onChange}
        webSearchAvailable={false}
      />,
    );
    expect(onChange).toHaveBeenCalledWith("knowledge");
  });
});

describe("useAsk payload contract", () => {
  it("forces web search only for explicit web mode", () => {
    const map = (sourceScope: "adaptive" | "knowledge" | "web") =>
      sourceScope === "web";
    expect(map("adaptive")).toBe(false);
    expect(map("web")).toBe(true);
    expect(map("knowledge")).toBe(false);
  });
});
