import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { slideInLeft } from "../../lib/motion";
import { BrandLogo } from "../brand/BrandLogo";
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
      aria-label={isStreaming ? "Answer based on sources being prepared" : "Based on sources"}
      aria-busy={isStreaming || undefined}
    >
      <div className="group relative w-full max-w-[var(--chat-assistant-max)]">
        <div className="assistantIdentity">
          {isError ? (
            <AlertTriangle size={16} strokeWidth={1.75} className="text-error self-center" aria-hidden />
          ) : null}
          {!isError ? (
            <BrandLogo variant="mark" decorative className="assistantIdentityMark" />
          ) : null}
          <span className="assistantIdentityName">AskMcNeese</span>
          {!isError ? <span className="assistantIdentityRole">Based on sources</span> : null}
          {message.timestamp && !isStreaming && (
            <span className="assistantIdentityTime">{formatTime(message.timestamp)}</span>
          )}
        </div>

        <SemanticAnswer message={message} />
        {!isError && !isStreaming ? (
          <p className="answerAuthorityNote">
            Use the cited McNeese page or office for official decisions.
          </p>
        ) : null}
        {!isError && !isStreaming && (
          <MessageActions
            text={message.text || message.structured?.contentMarkdown || ""}
          />
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