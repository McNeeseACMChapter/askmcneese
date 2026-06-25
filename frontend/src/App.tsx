import { useRef, useState, useEffect } from "react";
import { ChatInput } from "./components/ChatInput";
import { EmptyState } from "./components/EmptyState";
import { MessageBubble } from "./components/MessageBubble";
import { StatusBadge } from "./components/StatusBadge";
import { useAsk } from "./hooks/useAsk";
import { useHealth } from "./hooks/useHealth";
import type { ChatMessage } from "./types";

export default function App() {
  const { status, version } = useHealth();
  const { ask, loading } = useAsk();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text: string) {
    const userMsg: ChatMessage = { id: `u-${Date.now()}`, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);

    const { response, error } = await ask(text);

    if (response) {
      const reply: ChatMessage =
        response.chunks.length > 0
          ? {
              id: `a-${Date.now()}`,
              role: "assistant",
              text: "Retrieved from approved McNeese sources:",
              citations: response.chunks,
            }
          : {
              id: `a-${Date.now()}`,
              role: "assistant",
              text: "No matching information found in approved McNeese sources.",
            };
      setMessages((prev) => [...prev, reply]);
      return;
    }

    if (error) {
      const reply: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        text: `Sorry — I couldn't retrieve an answer. ${error}`,
      };
      setMessages((prev) => [...prev, reply]);
    }
  }

  return (
    <div className="flex h-full justify-center bg-slate-100 sm:items-center sm:py-6">
      <div className="flex h-full w-full flex-col bg-slate-50 shadow-xl sm:h-[640px] sm:max-w-md sm:overflow-hidden sm:rounded-2xl">
        {/* Brand bar */}
        <header className="bg-mcneese-blue px-4 py-3 text-white">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-bold tracking-tight">AskMcNeese</h1>
            <StatusBadge status={status} version={version} />
          </div>
          <p className="text-xs text-white/70">Your McNeese question assistant</p>
        </header>

        {/* Error state: backend unreachable */}
        {status === "offline" && (
          <div className="border-b border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">
            Backend is offline — start the API (<code>uvicorn app.main:app</code>) to connect.
          </div>
        )}

        {/* Chat panel */}
        <main className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}

          {/* Loading state: assistant is "thinking" */}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-sm border border-gray-200 bg-white px-4 py-2 text-sm text-gray-400">
                <span className="inline-flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.2s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.1s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400" />
                </span>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </main>

        <ChatInput onSend={handleSend} disabled={loading || status === "offline"} />

        {/* Attribution */}
        <footer className="bg-white py-2 text-center text-[11px] text-gray-400">
          Built by McNeese ACM
        </footer>
      </div>
    </div>
  );
}
