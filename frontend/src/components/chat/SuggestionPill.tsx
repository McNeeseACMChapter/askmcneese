import { motion } from "framer-motion";
import { pillHover, pillTap, listItem } from "../../lib/motion";

interface SuggestionPillProps {
  text: string;
  onClick: (text: string) => void;
}

export function SuggestionPill({ text, onClick }: SuggestionPillProps) {
  return (
    <motion.button
      variants={listItem}
      whileHover={pillHover}
      whileTap={pillTap}
      onClick={() => onClick(text)}
      className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2.5 text-sm text-text-secondary shadow-xs transition-all hover:border-mcneese-blue/30 hover:bg-primary-subtle hover:text-mcneese-blue hover:shadow-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-mcneese-blue/30"
    >
      <svg className="h-4 w-4 text-mcneese-gold flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
      <span>{text}</span>
    </motion.button>
  );
}
