import { useRef, useEffect, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { EmptyState } from "./EmptyState";
import type { ChatMessage } from "../../types";
import type { AskStatus, PipelineInfo } from "../../hooks/useAsk";

interface ChatPageProps {
  messages: ChatMessage[];
  isLoading: boolean;
  askStatus?: AskStatus;
  pipeline?: PipelineInfo;
  onSend: (text: string) => void;
}

export function ChatPage({ messages, isLoading, askStatus, pipeline, onSend }: ChatPageProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior });
  }, []);

  useEffect(() => {
    if (isAtBottomRef.current) {
      scrollToBottom();
    }
  }, [messages, isLoading, scrollToBottom]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    isAtBottomRef.current = scrollHeight - scrollTop - clientHeight < 100;
  };

  const handleSuggestionClick = (text: string) => {
    onSend(text);
  };

  return (
    <div className="flex flex-1 min-h-0 flex-col">
      <main
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 overflow-y-auto scrollbar-thin bg-background"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
        aria-relevant="additions"
      >
        <div className="mx-auto max-w-chat px-4 py-6 md:px-6 md:py-8">
          {messages.length === 0 ? (
            <EmptyState onSuggestionClick={handleSuggestionClick} />
          ) : (
            <div className="space-y-6">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <ChatBubble key={message.id} message={message} />
                ))}
              </AnimatePresence>
              <AnimatePresence>
                {isLoading && <TypingIndicator status={askStatus} pipeline={pipeline} />}
              </AnimatePresence>
            </div>
          )}
          <div ref={bottomRef} className="h-1" />
        </div>
      </main>

      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  );
}
