import { useCallback, useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { LiveAnswerProgress, runFromMessageSummary } from "./LiveAnswerProgress";
import { EmptyState } from "./EmptyState";
import type { AskRun } from "../../lib/askRun";
import type { ChatMessage, ComposerState, SourceScope } from "../../types";
import type { AskStatus } from "../../hooks/useAsk";

interface ChatPageProps {
  messages: ChatMessage[];
  isLoading: boolean;
  askStatus: AskStatus;
  offline: boolean;
  sourceScope: SourceScope;
  /** Active run owned by the provisional assistant message id. */
  activeRun: AskRun | null;
  onSend: (text: string) => void;
  onStop: () => void;
  onSourceScopeChange: (scope: SourceScope) => void;
  webSearchAvailable?: boolean;
  onOpenHistory?: () => void;
  onOpenSettings?: () => void;
}

export function ChatPage({
  messages,
  isLoading,
  askStatus,
  offline,
  sourceScope,
  activeRun,
  onSend,
  onStop,
  onSourceScopeChange,
  webSearchAvailable = true,
  onOpenHistory,
  onOpenSettings,
}: ChatPageProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);
  const empty = messages.length === 0;

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const scroller = scrollRef.current;
    if (scroller) {
      if (typeof scroller.scrollTo === "function") {
        scroller.scrollTo({ top: scroller.scrollHeight, behavior });
      } else {
        scroller.scrollTop = scroller.scrollHeight;
      }
      return;
    }
    bottomRef.current?.scrollIntoView?.({ behavior, block: "end" });
  }, []);

  // Keep the newest turn readable in the thread without sliding it under the sticky header.
  useEffect(() => {
    if (!activeRun) return;
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    requestAnimationFrame(() => {
      scrollToBottom(prefersReduced ? "auto" : "smooth");
    });
  }, [activeRun?.runId, scrollToBottom]);

  useEffect(() => {
    if (messages.length === 0) return;
    if (isAtBottomRef.current) {
      scrollToBottom();
    }
  }, [messages, isLoading, activeRun?.stages.length, scrollToBottom]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    isAtBottomRef.current = scrollHeight - scrollTop - clientHeight < 120;
  };

  return (
    <div
      className={`chatColumn flex h-full min-h-0 flex-1 flex-col${empty ? " chatColumn--welcome" : ""}`}
    >
      <main
        ref={scrollRef}
        onScroll={handleScroll}
        className="chatThread min-h-0 flex-1 overflow-y-auto overscroll-contain scrollbar-thin"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
        aria-relevant="additions"
      >
        <div
          className={`chatThreadInner mx-auto ${empty ? "flex min-h-full flex-col" : "pb-2 pt-4 md:pb-3 md:pt-5"}`}
          style={{
            width: "min(calc(100% - (2 * var(--page-gutter))), var(--chat-max-width))",
            maxWidth: "var(--chat-max-width)",
          }}
        >
          {empty ? (
            <EmptyState onSuggestionClick={onSend} />
          ) : (
            <div className="chatMessageStack">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => {
                  const runForMessage = resolveRunForMessage(message, activeRun);
                  return (
                    <div
                      key={message.id}
                      className="chatTurn"
                      data-message-id={message.id}
                      data-run-id={runForMessage?.runId}
                    >
                      {message.role === "assistant" && runForMessage && (
                        <div className="flex justify-start">
                          <LiveAnswerProgress
                            key={runForMessage.runId}
                            run={runForMessage}
                          />
                        </div>
                      )}
                      <ChatBubble message={message} />
                    </div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
          <div ref={bottomRef} className="chatThreadEndSpacer" aria-hidden="true" />
        </div>
      </main>

      <ChatInput
        onSend={onSend}
        onStop={onStop}
        loading={isLoading}
        offline={offline}
        state={toComposerState(askStatus, offline)}
        sourceScope={sourceScope}
        onSourceScopeChange={onSourceScopeChange}
        webSearchAvailable={webSearchAvailable}
        onOpenHistory={onOpenHistory}
        onOpenSettings={onOpenSettings}
      />
    </div>
  );
}

function resolveRunForMessage(
  message: ChatMessage,
  activeRun: AskRun | null,
): AskRun | null {
  if (message.role !== "assistant") return null;
  if (activeRun && activeRun.assistantMessageId === message.id) {
    return activeRun;
  }
  if (message.runSummary) {
    return runFromMessageSummary(message.id, message.runSummary);
  }
  return null;
}

function toComposerState(status: AskStatus, offline: boolean): ComposerState {
  if (offline) return "offline";
  if (status === "connecting") return "submitting";
  if (status === "searching") return "retrieving";
  if (status === "generating") return "generating";
  if (status === "stopped") return "stopped";
  if (status === "error") return "failed";
  return "idle";
}
