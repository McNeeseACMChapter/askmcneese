import { motion } from "framer-motion";
import { slideInRight } from "../../lib/motion";
import { AssistantMessage } from "./AssistantMessage";
import type { ChatMessage } from "../../types";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  if (!isUser) {
    return <AssistantMessage message={message} />;
  }

  return (
    <motion.article
      variants={slideInRight}
      initial="hidden"
      animate="visible"
      className="chatTurnUser flex justify-end"
      role="article"
      aria-label={`You said: ${message.text.slice(0, 50)}`}
    >
      {/* Fit content — never stretch short prompts into a sticky-note slab */}
      <div className="userMessageShell">
        <div className="userMessage">
          <p className="userMessageText">{message.text}</p>
        </div>
        {message.timestamp && (
          <p className="userMessageTime">{formatTime(message.timestamp)}</p>
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
