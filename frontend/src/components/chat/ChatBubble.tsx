import { useState } from "react";
import { motion } from "framer-motion";
import { slideInLeft, slideInRight } from "../../lib/motion";
import { CitationCard } from "./CitationCard";
import type { ChatMessage } from "../../types";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.article
      variants={isUser ? slideInRight : slideInLeft}
      initial="hidden"
      animate="visible"
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      role="article"
      aria-label={`${isUser ? "You" : "Assistant"} said: ${message.text.slice(0, 50)}...`}
    >
      <div className={`group relative max-w-message ${isUser ? "ml-8" : "mr-8"}`}>
        {!isUser && (
          <div className="mb-1 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-mcneese-blue to-mcneese-dark">
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-xs font-medium text-text-secondary">AskMcNeese</span>
            {message.isDemo && (
              <span className="rounded-full bg-mcneese-gold/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-mcneese-gold">
                Demo
              </span>
            )}
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-soft ${
            isUser
              ? "rounded-br-md bg-mcneese-blue text-white"
              : "rounded-bl-md border border-border bg-surface text-text-primary"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.text}</p>
        </div>

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 space-y-1.5">
            {message.citations.map((citation) => (
              <CitationCard key={citation.id} citation={citation} />
            ))}
          </div>
        )}

        {!isUser && (
          <div className="mt-1.5 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 md:opacity-0">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-text-muted hover:bg-gray-100 hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-mcneese-blue/30"
              aria-label={copied ? "Copied!" : "Copy message"}
            >
              {copied ? (
                <>
                  <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-emerald-600">Copied</span>
                </>
              ) : (
                <>
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}

        {message.timestamp && (
          <p className={`mt-1 text-[10px] text-text-muted ${isUser ? "text-right" : "text-left"}`}>
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
