import { useRef, useState, useEffect } from "react";
import { AskLoadingSkeleton } from "./components/skeleton";
import { ChatInput } from "./components/ChatInput";
import { EmptyState } from "./components/EmptyState";
import { Header } from "./components/Header";
import { MessageBubble } from "./components/MessageBubble";
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
    <div className="flex h-[100dvh] min-h-0 justify-center bg-[var(--bg-page)] sm:h-full sm:items-center sm:py-6">
      <div className="flex h-full min-h-0 w-full flex-col bg-[var(--bg-surface)] shadow-xl sm:h-[640px] sm:max-w-md sm:overflow-hidden sm:rounded-2xl">
        <Header status={status} version={version} />

        {status === "offline" && (
          <div className="border-b border-[var(--error-border)] bg-[var(--error-bg)] px-4 py-2 text-xs text-[var(--error-text)]">
            Backend is offline — start the API (<code>uvicorn app.main:app</code>) to connect.
          </div>
        )}

        <main className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}

          {loading && <AskLoadingSkeleton />}
          <div ref={endRef} />
        </main>

        <ChatInput onSend={handleSend} disabled={loading || status === "offline"} />

        {/* Attribution */}
        <footer className="app-footer bg-[var(--bg-card)] py-2 text-center text-[11px] text-[var(--text-muted)]">
          Built by McNeese ACM
        </footer>
      </div>
    </div>
  );
}
