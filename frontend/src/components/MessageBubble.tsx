import type { ChatMessage } from "../types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm leading-relaxed shadow-sm ${
          isUser
            ? "rounded-br-sm bg-mcneese-blue text-white"
            : "rounded-bl-sm border border-gray-200 bg-white text-gray-800"
        }`}
      >
        {message.isDemo && !isUser && (
          <span className="mb-1 block text-[10px] font-bold uppercase tracking-wide text-mcneese-gold">
            Demo
          </span>
        )}
        {message.text}
      </div>
    </div>
  );
}
