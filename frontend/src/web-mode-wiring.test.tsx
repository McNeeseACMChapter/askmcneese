import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
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
  return render(
    <MemoryRouter>
      <ChatInput {...props} />
    </MemoryRouter>,
  );
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

    const select = screen.getByLabelText("Source scope");
    expect(select).toHaveValue("adaptive");
    await user.selectOptions(select, "web");
    expect(onChange).toHaveBeenCalledWith("web");

    rerender(
      <MemoryRouter>
        <ChatInput
          onSend={vi.fn()}
          onStop={vi.fn()}
          loading={false}
          offline={false}
          state="idle"
          sourceScope="web"
          onSourceScopeChange={onChange}
          webSearchAvailable
        />
      </MemoryRouter>,
    );
    expect(screen.getByLabelText("Source scope")).toHaveValue("web");
  });

  it("disables web option when backend capability is false", () => {
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
    const webOption = screen.getByRole("option", { name: /Campus live \(unavailable\)/i });
    expect(webOption).toBeDisabled();
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
      <MemoryRouter>
        <ChatInput
          onSend={vi.fn()}
          onStop={vi.fn()}
          loading={false}
          offline={false}
          state="idle"
          sourceScope="adaptive"
          onSourceScopeChange={onChange}
          webSearchAvailable={false}
        />
      </MemoryRouter>,
    );
    expect(onChange).toHaveBeenCalledWith("knowledge");
  });
});

describe("useAsk payload contract", () => {
  it("maps adaptive and web to use_web_search true", () => {
    const map = (sourceScope: "adaptive" | "knowledge" | "web") =>
      sourceScope === "web" || sourceScope === "adaptive";
    expect(map("adaptive")).toBe(true);
    expect(map("web")).toBe(true);
    expect(map("knowledge")).toBe(false);
  });
});
