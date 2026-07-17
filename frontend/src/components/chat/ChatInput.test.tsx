import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { ChatInput } from "./ChatInput";
import type { ComposerState, SourceScope } from "../../types";

const PROMPT_LIMIT = 1000;

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
    onOpenHistory: () => void;
    onOpenSettings: () => void;
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
    onOpenHistory: vi.fn(),
    onOpenSettings: vi.fn(),
    ...overrides,
  };
  const result = render(
    <MemoryRouter>
      <ChatInput {...props} />
    </MemoryRouter>,
  );
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
    expect(screen.getByLabelText("Source scope")).toBeDisabled();
  });

  it("Send becomes Stop while loading", () => {
    renderInput({ loading: true, state: "generating" });
    expect(screen.getByRole("button", { name: /Stop response/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Send question/i })).not.toBeInTheDocument();
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
    await user.selectOptions(screen.getByLabelText("Source scope"), "web");
    expect(props.onSourceScopeChange).toHaveBeenCalledWith("web");
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
  it("represents the 1000-character limit in the UI near the threshold", () => {
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    fireEvent.change(box, { target: { value: "a".repeat(820) } });
    expect(screen.getByText(/820\s*\/\s*1000/)).toBeInTheDocument();
    expect(box).toHaveAttribute("maxLength", String(PROMPT_LIMIT));
  });

  it("over-limit input cannot submit", () => {
    const { props } = renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    fireEvent.change(box, { target: { value: "a".repeat(PROMPT_LIMIT + 1) } });
    expect(screen.getByRole("button", { name: /Send question/i })).toBeDisabled();
    fireEvent.keyDown(box, { key: "Enter", code: "Enter" });
    expect(props.onSend).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/1000 characters/i);
  });
});

describe("ChatInput refine chips and chrome", () => {
  it("refinement chips modify the current draft without submitting", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    await user.click(screen.getByRole("button", { name: /Refine question/i }));
    await user.click(screen.getByRole("button", { name: /Include deadlines/i }));
    expect(props.onSend).not.toHaveBeenCalled();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i });
    expect((box as HTMLTextAreaElement).value).toMatch(/deadlines/i);
  });

  it("history invokes the real supplied callback", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    await user.click(screen.getByRole("button", { name: /Open conversation history/i }));
    expect(props.onOpenHistory).toHaveBeenCalledTimes(1);
  });

  it("settings invokes real navigation or its supplied callback", async () => {
    const user = userEvent.setup();
    const { props } = renderInput();
    await user.click(screen.getByRole("button", { name: /Open settings/i }));
    expect(props.onOpenSettings).toHaveBeenCalledTimes(1);
  });

  it("keeps history and settings in the compact toolbar utilities", () => {
    renderInput();
    expect(screen.getByTestId("composer-utilities")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Open conversation history/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Open settings/i })).toBeInTheDocument();
  });

  it("grows the textarea height from content without a fixed clipping parent", async () => {
    const user = userEvent.setup();
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i }) as HTMLTextAreaElement;
    Object.defineProperty(box, "scrollHeight", { configurable: true, get: () => 96 });
    await user.type(box, "Line one{Shift>}{Enter}{/Shift}Line two{Shift>}{Enter}{/Shift}Line three");
    expect(box).toHaveValue("Line one\nLine two\nLine three");
    expect(box).not.toHaveClass("max-h-36");
    expect(box.style.height).toBe("96px");
    expect(box.style.overflowY).toBe("hidden");
  });

  it("caps textarea growth and enables internal scroll past the max", async () => {
    const user = userEvent.setup();
    renderInput();
    const box = screen.getByRole("textbox", { name: /AskMcNeese question/i }) as HTMLTextAreaElement;
    Object.defineProperty(box, "scrollHeight", { configurable: true, get: () => 240 });
    await user.type(box, "Tall content");
    expect(box.style.height).toBe("112px");
    expect(box.style.overflowY).toBe("auto");
  });

  it("does not render model, agent, attachment, microphone, or deep-research controls", () => {
    renderInput();
    expect(screen.queryByRole("button", { name: /attach|microphone|deep research|experimental/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/GPT-|Claude|Gemini/i)).not.toBeInTheDocument();
  });
});
