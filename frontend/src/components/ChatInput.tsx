import { useState, type FormEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2 border-t border-gray-200 bg-white p-3"
    >
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about admissions, deadlines, financial aid…"
        aria-label="Type your question"
        className="flex-1 rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-mcneese-blue focus:outline-none focus:ring-1 focus:ring-mcneese-blue"
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
