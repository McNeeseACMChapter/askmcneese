import { motion } from "framer-motion";
import { slideInLeft } from "../../lib/motion";
import { AnswerCard } from "./AnswerCard";
import { CitationGroup } from "./CitationGroup";
import { MessageActions } from "./MessageActions";
import type { ChatMessage } from "../../types";

interface AssistantMessageProps {
  message: ChatMessage;
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  const isError = message.isError === true;

  return (
    <motion.article
      variants={slideInLeft}
      initial="hidden"
      animate="visible"
      className="flex justify-start"
      role="article"
      aria-label={`Assistant response`}
    >
      <div className="group relative max-w-message">
        {/* Assistant identity */}
        <div className="mb-2 flex items-center gap-2">
          <div className={`flex h-6 w-6 items-center justify-center rounded-lg ${isError ? 'bg-error' : 'bg-mcneese-blue'}`}>
            {isError ? (
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            ) : (
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
              </svg>
            )}
          </div>
          <span className="text-xs font-medium text-text-secondary">AskMcNeese</span>
          {message.isDemo && (
            <span className="rounded-full bg-accent-subtle px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-mcneese-gold">
              Demo
            </span>
          )}
          {message.confidence === "low" && !isError && (
            <span className="rounded-full bg-warning/10 px-2 py-0.5 text-[10px] font-semibold text-warning">
              Limited sources
            </span>
          )}
        </div>

        {/* Error state - simple message */}
        {isError ? (
          <div className="rounded-2xl rounded-bl-md border border-error/30 bg-error/5 px-4 py-3 text-sm text-text-primary">
            <p>{message.text}</p>
          </div>
        ) : (
          <>
            {/* Answer card */}
            <AnswerCard content={message.text} />

            {/* Citations */}
            {message.citations && message.citations.length > 0 && (
              <CitationGroup citations={message.citations} />
            )}

            {/* Actions */}
            <MessageActions text={message.text} />
          </>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <p className="mt-1 text-[10px] text-text-muted">
            {formatTime(message.timestamp)}
          </p>
        )}
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
