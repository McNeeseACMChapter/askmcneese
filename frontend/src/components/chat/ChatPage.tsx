import { useCallback, useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { LiveAnswerProgress, runFromMessageSummary } from "./LiveAnswerProgress";
import { EmptyState } from "./EmptyState";
import type { AskRun } from "../../lib/askRun";
import type { ChatMessage, ComposerState, SourceScope } from "../../types";
import type { AskRequestVisualState, AskStatus } from "../../hooks/useAsk";
import "../../styles/ask-experience.css";

interface ChatPageProps {
  messages: ChatMessage[];
  isLoading: boolean;
  askStatus: AskStatus;
  offline: boolean;
  sourceScope: SourceScope;
  /** Active run owned by the provisional assistant message id. */
  activeRun: AskRun | null;
  /** Request-scoped visual lifecycle from useAsk. */
  requestVisualState: AskRequestVisualState;
  onSend: (text: string) => void;
  onStop: () => void;
  onSourceScopeChange: (scope: SourceScope) => void;
  webSearchAvailable?: boolean;
}

export function ChatPage({
  messages,
  isLoading,
  askStatus,
  offline,
  sourceScope,
  activeRun,
  requestVisualState,
  onSend,
  onStop,
  onSourceScopeChange,
  webSearchAvailable = true,
}: ChatPageProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);
  const empty = messages.length === 0;

  /*
   * Request animation stays on through useAsk phase AND until App commits the
   * final assistant turn (activeRun cleared / no longer running). Phase alone
   * would fade in useAsk's finally a tick before setMessages merges the answer.
   */
  const liveDockRun =
    activeRun &&
    (activeRun.status === "queued" ||
      activeRun.status === "running" ||
      activeRun.status === "streaming")
      ? activeRun
      : null;


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

  // Anchor when the user is near the bottom and answer text meaningfully grows.
  const lastAssistantTextLen = messages.reduce((len, message) => {
    if (message.role !== "assistant") return len;
    return Math.max(len, message.text.length);
  }, 0);

  useEffect(() => {
    if (messages.length === 0 || !isAtBottomRef.current) return;
    // While a run is live, the trail stays docked at the top — do not yank down.
    if (liveDockRun) return;
    requestAnimationFrame(() => scrollToBottom("auto"));
  }, [
    messages.length,
    lastAssistantTextLen,
    isLoading,
    liveDockRun,
    scrollToBottom,
  ]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    isAtBottomRef.current = scrollHeight - scrollTop - clientHeight < 120;
  };

  return (
    <div
      className={`chatColumn flex h-full min-h-0 flex-1 flex-col${empty ? " chatColumn--welcome" : ""}`}
      data-request-phase={requestVisualState.phase}
    >

      <div className="chatColumn__foreground">
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
            className={`chatThreadInner mx-auto ${
              empty ? "chatThreadInner--welcome flex h-full min-h-full flex-col" : "pb-2 pt-4 md:pb-3 md:pt-5"
            }`}
            style={{
              width: "min(calc(100% - (2 * var(--page-gutter))), var(--chat-max-width))",
              maxWidth: "var(--chat-max-width)",
            }}
          >
            {empty ? (
              <EmptyState onSuggestion={onSend} />
            ) : (
              <>
                <div className="chatMessageStack">
                  <AnimatePresence mode="popLayout">
                    {messages.map((message) => {
                      const runForMessage = resolveRunForMessage(message, activeRun);

                      const hasAssistantContent =
                        message.role !== "assistant" ||
                        Boolean(message.text.trim()) ||
                        Boolean(message.structured?.contentMarkdown?.trim()) ||
                        message.isError === true ||
                        (!runForMessage && message.isStreaming !== true);

                      return (
                        <div
                          key={message.id}
                          className="chatTurn"
                          data-message-id={message.id}
                          data-run-id={runForMessage?.runId}
                        >
                          {message.role === "assistant" && runForMessage ? (

                            <div className="flex justify-start">
                              <LiveAnswerProgress key={runForMessage.runId} run={runForMessage} />
                            </div>
                          ) : null}

                          {hasAssistantContent ? <ChatBubble message={message} /> : null}
                        </div>
                      );
                    })}
                  </AnimatePresence>
                </div>
                <div ref={bottomRef} className="chatThreadEndSpacer" aria-hidden="true" />
              </>
            )}
          </div>
        </main>

        <div>
          <ChatInput
            onSend={onSend}
            onStop={onStop}
            loading={isLoading}
            offline={offline}
            state={toComposerState(askStatus, offline)}
            sourceScope={sourceScope}
            onSourceScopeChange={onSourceScopeChange}
            webSearchAvailable={webSearchAvailable}
          />
        </div>
      </div>
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
