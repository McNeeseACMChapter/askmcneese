import { motion } from "framer-motion";
import { slideInLeft } from "../../lib/motion";
import type { AskStatus } from "../../hooks/useAsk";
import type { ActivityEvent } from "../../types";
import { ActivityTimeline } from "./ActivityTimeline";

interface TypingIndicatorProps {
  status?: AskStatus;
  activity?: ActivityEvent[];
}

export function TypingIndicator({ status = "searching", activity = [] }: TypingIndicatorProps) {
  const hasActivity = activity.length > 0;
  const currentMessage = hasActivity
    ? activity[activity.length - 1]?.message
    : getDefaultMessage(status);

  return (
    <motion.div
      variants={slideInLeft}
      initial="hidden"
      animate="visible"
      exit="exit"
      className="flex justify-start"
      role="status"
      aria-live="polite"
      aria-label={currentMessage || "Preparing your answer"}
    >
      <div className="flex w-full max-w-[var(--chat-assistant-max)] items-start gap-2">
        <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--chat-accent)]">
          <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
            />
          </svg>
        </div>

        {hasActivity ? (
          <ActivityTimeline events={activity} disconnected={status === "error"} />
        ) : (
          <div className="activityBubble">
            <p className="activityBubbleText">
              <span className="typingDots" aria-hidden="true">
                <span className="typingDot active" />
                <span className="typingDot" />
                <span className="typingDot" />
              </span>
              {currentMessage}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function getDefaultMessage(status: AskStatus): string {
  switch (status) {
    case "connecting":
      return "Got your question — starting now";
    case "searching":
      return "Searching McNeese-approved sources";
    case "generating":
      return "Writing your answer from those sources";
    case "complete":
      return "Answer ready";
    case "stopped":
      return "Stopped";
    case "error":
      return "Something went wrong — please try again";
    default:
      return "Reading your question to decide what to search";
  }
}
