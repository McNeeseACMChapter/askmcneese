import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { slideInLeft } from "../../lib/motion";
import { SemanticAnswer } from "./SemanticAnswer";
import { MessageActions } from "./MessageActions";
import type { ChatMessage } from "../../types";

interface AssistantMessageProps {
  message: ChatMessage;
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  const isError = message.isError === true;
  const isStreaming = message.isStreaming === true;

  return (
    <motion.article
      variants={slideInLeft}
      initial="hidden"
      animate="visible"
      className="flex justify-start"
      role="article"
      aria-label={isStreaming ? "Assistant response generating" : "Assistant response"}
      aria-busy={isStreaming || undefined}
    >
      <div className="group relative w-full max-w-[var(--chat-assistant-max)]">
        <div className="assistantIdentity mb-2 flex flex-wrap items-baseline gap-x-2 gap-y-1">
          {isError ? (
            <AlertTriangle size={16} strokeWidth={1.75} className="text-error self-center" aria-hidden />
          ) : null}
          <span className="font-editorial text-[0.9375rem] font-semibold tracking-[-0.01em] text-text-primary">
            AskMcNeese
          </span>
          {isStreaming && (
            <span className="font-sans text-xs font-medium text-brand-700">Writing…</span>
          )}
          {message.timestamp && !isStreaming && (
            <span className="font-sans text-xs text-text-muted">{formatTime(message.timestamp)}</span>
          )}
        </div>

        <SemanticAnswer message={message} />
        {!isError && !isStreaming && <MessageActions text={message.text} />}
      </div>
    </motion.article>
  );
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}
