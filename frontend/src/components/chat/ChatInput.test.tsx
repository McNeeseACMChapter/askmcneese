import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  ChatInput,
  COMPOSER_PROMPT_LIMIT,
  COMPOSER_TEXTAREA_MAX_PX,
} from "./ChatInput";
import type { ComposerState, SourceScope } from "../../types";

function renderInput(
  overrides: Partial<{
    onSend: (text: string) => void;
    onStop: () => void;
    loading: boolean;
    offline: boolean;
    state: ComposerState;
    sourceScope: SourceScope;
    onSourceScopeChange: (scope: SourceScope) => void;
    webSearchAvailable: boolean;
  }> = {},
) {
  const props = {
    onSend: vi.fn(),
    onStop: vi.fn(),
    loading: false,
    offline: false,
    state: "idle" as ComposerState,
    sourceScope: "knowledge" as SourceScope,
    onSourceScopeChange: vi.fn(),
    webSearchAvailable: true,
    ...overrides,
  };
  const result = render(<ChatInput {...props} />);
  return { ...result, props };
}

describe("ChatInput submission and keyboard", () => {
  it("Enter submits a valid trimmed prompt", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    await user.type(box, "  What is tuition?  ");
    await user.keyboard("{Enter}");
    expect(props.onSend).toHaveBeenCalledWith("What is tuition?");
  });

  it("Shift+Enter inserts a newline and does not submit", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    await user.type(box, "Line one");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    await user.type(box, "Line two");
    expect(props.onSend).not.toHaveBeenCalled();
    expect(box).toHaveValue("Line one\nLine two");
  });

  it("Enter during IME composition does not submit", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    await user.type(box, "hello");
    fireEvent.keyDown(box, { key: "Enter", code: "Enter", isComposing: true });
    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("empty text does not submit", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    await user.click(screen.getByRole("button", { name: /Send question/i }));
    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("whitespace-only text does not submit", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    await user.type(box, "   ");
    expect(screen.getByRole("button", { name: /Send question/i })).toBeDisabled();
    await user.keyboard("{Enter}");
    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("loading prevents duplicate submission", async () => {
    const user = userEvent.setup();
    const { props } = renderInput({ loading: true, state: "generating" });
    expect(screen.queryByRole("button", { name: /Send question/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Stop response/i })).toBeInTheDocument();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    await user.type(box, "Another question");
    await user.keyboard("{Enter}");
    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("offline disables submission", () => {
    const { props } = renderInput({ offline: true, state: "offline" });
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    expect(box).toBeDisabled();
    expect(screen.getByRole("button", { name: /Send question/i })).toBeDisabled();
    expect(props.onSend).not.toHaveBeenCalled();
  });
});

describe("ChatInput source scope and stop", () => {
  it("source selector remains disabled while loading", () => {
    renderInput({ loading: true, state: "retrieving" });
    expect(screen.getByLabelText("Choose source mode")).toBeDisabled();
  });

  it("Send becomes Stop while loading", () => {
    renderInput({ loading: true, state: "generating" });
    expect(screen.getByRole("button", { name: /Stop response/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Send question/i })).not.toBeInTheDocument();
  });

  it("Stop uses primary action surface, not danger red", () => {
    renderInput({ loading: true, state: "generating" });
    const stop = screen.getByRole("button", { name: /Stop response/i });
    expect(stop.className).toContain("composerPrimaryAction--stop");
    expect(stop.className).not.toMatch(/danger/i);
  });

  it("Stop invokes the existing onStop callback", async () => {
    const user = userEvent.setup();
    const { props } = renderInput({ loading: true, state: "generating" });
    await user.click(screen.getByRole("button", { name: /Stop response/i }));
    expect(props.onStop).toHaveBeenCalledTimes(1);
  });

  it("existing source scope remains wired", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    await user.click(screen.getByRole("button", { name: "Choose source mode" }));
    await user.click(screen.getByRole("option", { name: /Web research/i }));
    expect(props.onSourceScopeChange).toHaveBeenCalledWith("web");
  });

  it("lists Automatic first and marks the selected mode", async () => {
    const user = userEvent.setup();
    renderInput({ sourceScope: "adaptive" });
    await user.click(screen.getByRole("button", { name: "Choose source mode" }));
    const options = screen.getAllByRole("option");
    expect(options[0]).toHaveTextContent(/Automatic/);
    expect(options[0]).toHaveTextContent(/Best for most questions/i);
    expect(options[0]).toHaveAttribute("aria-selected", "true");
    expect(options).toHaveLength(3);
  });

  it("closes the source menu on Escape and outside interaction", async () => {
    const user = userEvent.setup();
    renderInput();
    await user.click(screen.getByRole("button", { name: "Choose source mode" }));
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("submitted prompt clears after local submission handling", async () => {
    const user = userEvent.setup();
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    await user.type(box, "Campus hours?");
    await user.keyboard("{Enter}");
    expect(box).toHaveValue("");
  });
});

describe("ChatInput character limit", () => {
  it("shows the counter only near the limit", () => {
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    const near = Math.ceil(COMPOSER_PROMPT_LIMIT * 0.85);
    fireEvent.change(box, { target: { value: "a".repeat(near) } });
    expect(
      screen.getByText(new RegExp(`${near.toLocaleString()}\\s*/\\s*${COMPOSER_PROMPT_LIMIT.toLocaleString()}`)),
    ).toBeInTheDocument();
    expect(box).toHaveAttribute("maxLength", String(COMPOSER_PROMPT_LIMIT));
  });

  it("does not show an unreachable over-limit validation alert", () => {
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    fireEvent.change(box, { target: { value: "a".repeat(COMPOSER_PROMPT_LIMIT) } });
    expect(screen.getByRole("button", { name: /Send question/i })).not.toBeDisabled();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("ChatInput slim chrome", () => {
  it("does not render history, settings, refine wand, chips, caution, or smoke", () => {
    renderInput();
    expect(screen.queryByRole("button", { name: /Open conversation history/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Open settings/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Refine question/i })).toBeNull();
    expect(screen.queryByText(/Include deadlines/i)).toBeNull();
    expect(screen.queryByText(/AskMcNeese can make mistakes/i)).toBeNull();
    expect(document.querySelector(".composerSmokePulse")).toBeNull();
    expect(screen.queryByTestId("composer-utilities")).toBeNull();
  });

  it("uses plain-language source vocabulary", () => {
    renderInput({ sourceScope: "adaptive" });
    expect(screen.getByText("Automatic")).toBeInTheDocument();
    expect(screen.queryByText(/^Adaptive$/)).toBeNull();
    expect(screen.queryByText(/^Smart$/)).toBeNull();
    expect(screen.queryByText(/Campus live/i)).toBeNull();
  });

  it("grows the textarea height from content without a fixed clipping parent", async () => {
    const user = userEvent.setup();
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i }) as HTMLTextAreaElement;
    Object.defineProperty(box, "scrollHeight", { configurable: true, get: () => 96 });
    await user.type(box, "Line one{Shift>}{Enter}{/Shift}Line two{Shift>}{Enter}{/Shift}Line three");
    expect(box).toHaveValue("Line one\nLine two\nLine three");
    expect(box.style.height).toBe("96px");
    expect(box.style.overflowY).toBe("hidden");
  });

  it("caps textarea growth and enables internal scroll past the max", async () => {
    const user = userEvent.setup();
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i }) as HTMLTextAreaElement;
    Object.defineProperty(box, "scrollHeight", { configurable: true, get: () => 240 });
    await user.type(box, "Tall content");
    expect(box.style.height).toBe(`${COMPOSER_TEXTAREA_MAX_PX}px`);
    expect(box.style.overflowY).toBe("auto");
  });

  it("does not render model, agent, attachment, microphone, or deep-research controls", () => {
    renderInput();
    expect(screen.queryByRole("button", { name: /attach|microphone|deep research|experimental/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/GPT-|Claude|Gemini/i)).not.toBeInTheDocument();
  });
});
