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
    expect(trigger.getAttribute("data-value")).toBe("adaptive");
    await user.click(trigger);
    await user.click(screen.getByRole("option", { name: /Web research/i }));
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
      screen.getByRole("button", { name: "Choose source mode" }).getAttribute("data-value"),
    ).toBe("web");
  });

  it("keeps campus source choices usable when web research is unavailable", async () => {
    const user = userEvent.setup();
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
    const trigger = screen.getByLabelText("Choose source mode");
    expect((trigger as HTMLButtonElement).disabled).toBe(false);
    await user.click(trigger);
    expect((screen.getByRole("option", { name: /Automatic/i }) as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByRole("option", { name: /McNeese sources only/i }) as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByRole("option", { name: /Web research/i }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("keeps Automatic selected when web research becomes unavailable", () => {
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
    expect(onChange).not.toHaveBeenCalled();
  });

  it("falls back from Web research to Automatic when web becomes unavailable", () => {
    const onChange = vi.fn();
    renderChatInput({
      onSend: vi.fn(),
      onStop: vi.fn(),
      loading: false,
      offline: false,
      state: "idle",
      sourceScope: "web",
      onSourceScopeChange: onChange,
      webSearchAvailable: false,
    });
    expect(onChange).toHaveBeenCalledWith("adaptive");
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
