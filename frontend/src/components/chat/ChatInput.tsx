import { useState, useRef, useEffect, type KeyboardEvent, type FormEvent } from "react";
import { motion } from "framer-motion";
import { buttonHover, buttonTap } from "../../lib/motion";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled = false, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [value]);

  useEffect(() => {
    if (!disabled) {
      textareaRef.current?.focus();
    }
  }, [disabled]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div className="border-t border-border bg-surface/80 backdrop-blur-sm px-4 pb-safe pt-3">
      <form onSubmit={handleSubmit} className="mx-auto max-w-chat">
        <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-background p-2 shadow-soft transition-shadow focus-within:border-mcneese-blue/40 focus-within:shadow-card">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder ?? "Ask anything about McNeese..."}
            disabled={disabled}
            rows={1}
            aria-label="Message input"
            aria-describedby="input-hint"
            className="max-h-[120px] min-h-[40px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
          />
          <span id="input-hint" className="sr-only">
            Press Enter to send, Shift+Enter for new line
          </span>
          <motion.button
            type="submit"
            disabled={!canSend}
            whileHover={canSend ? buttonHover : undefined}
            whileTap={canSend ? buttonTap : undefined}
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-mcneese-blue text-white transition-all hover:bg-mcneese-dark focus:outline-none focus:ring-2 focus:ring-mcneese-blue/40 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Send message"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </motion.button>
        </div>
        <p className="mt-2 text-center text-[11px] text-text-muted">
          Answers sourced from official McNeese pages • Press Enter to send
        </p>
      </form>
    </div>
  );
}
