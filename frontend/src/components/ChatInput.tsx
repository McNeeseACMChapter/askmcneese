import { useEffect, useRef, useState, type FormEvent, type RefObject } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

/** Keeps the input bar visible when the mobile virtual keyboard opens. */
function useMobileKeyboardInset(formRef: RefObject<HTMLFormElement | null>) {
  useEffect(() => {
    const viewport = window.visualViewport;
    if (!viewport) return;

    function syncKeyboardInset() {
      const overlap = Math.max(
        0,
        window.innerHeight - viewport.height - viewport.offsetTop,
      );
      document.documentElement.style.setProperty(
        "--keyboard-inset",
        `${overlap}px`,
      );

      if (document.activeElement instanceof HTMLElement) {
        formRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
      }
    }

    viewport.addEventListener("resize", syncKeyboardInset);
    viewport.addEventListener("scroll", syncKeyboardInset);

    return () => {
      viewport.removeEventListener("resize", syncKeyboardInset);
      viewport.removeEventListener("scroll", syncKeyboardInset);
      document.documentElement.style.setProperty("--keyboard-inset", "0px");
    };
  }, [formRef]);
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useMobileKeyboardInset(formRef);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  }

  function handleFocus() {
    requestAnimationFrame(() => {
      inputRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      formRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
    });
  }

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit}
      className="chat-input-bar flex items-center gap-2 border-t border-[var(--border)] bg-[var(--bg-card)] px-3 pt-3"
      style={{ marginBottom: "var(--keyboard-inset)" }}
    >
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onFocus={handleFocus}
        enterKeyHint="send"
        placeholder="Ask about admissions, deadlines, financial aid…"
        aria-label="Type your question"
        className="flex-1 rounded-full border border-[var(--border)] bg-[var(--bg-input)] px-4 py-2 text-base text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-mcneese-blue focus:outline-none focus:ring-1 focus:ring-mcneese-blue sm:text-sm"
      />
      <button
        type="submit"
        disabled={disabled || value.trim().length === 0}
        className="rounded-full bg-mcneese-blue px-4 py-2 text-sm font-semibold text-white transition hover:bg-mcneese-dark disabled:cursor-not-allowed disabled:opacity-50"
      >
        Send
      </button>
    </form>
  );
}
