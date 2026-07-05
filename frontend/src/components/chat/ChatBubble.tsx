import { motion } from "framer-motion";
import { slideInRight } from "../../lib/motion";
import { AssistantMessage } from "./AssistantMessage";
import type { ChatMessage } from "../../types";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  // Use the new AssistantMessage component for assistant responses
  if (!isUser) {
    return <AssistantMessage message={message} />;
  }

  // User message - simple bubble
  return (
    <motion.article
      variants={slideInRight}
      initial="hidden"
      animate="visible"
      className="flex justify-end"
      role="article"
      aria-label={`You said: ${message.text.slice(0, 50)}...`}
    >
      <div className="relative max-w-message ml-8">
        <div className="rounded-2xl rounded-br-md bg-mcneese-blue px-4 py-3 text-sm leading-relaxed text-white shadow-soft">
          <p className="whitespace-pre-wrap">{message.text}</p>
        </div>

        {message.timestamp && (
          <p className="mt-1 text-[10px] text-text-muted text-right">
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
