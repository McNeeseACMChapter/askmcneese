import { motion } from "framer-motion";
import { fadeIn, staggerContainer } from "../../lib/motion";
import { SuggestionPill } from "./SuggestionPill";

interface EmptyStateProps {
  onSuggestionClick: (text: string) => void;
}

const suggestions = [
  "When is the application deadline?",
  "How do I apply for financial aid?",
  "What scholarships are available?",
  "Where is the registrar's office?",
];

export function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="flex h-full flex-col items-center justify-center px-4 py-12"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-mcneese-blue to-mcneese-dark shadow-card"
      >
        <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
          />
        </svg>
      </motion.div>

      <motion.div
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="mb-8 text-center"
      >
        <h2 className="mb-2 text-2xl font-bold text-text-primary">
          Howdy! <span className="inline-block animate-bounce">👋</span>
        </h2>
        <p className="mx-auto max-w-sm text-sm text-text-secondary">
          I'm your McNeese assistant. Ask me about admissions, financial aid, campus services, or anything McNeese-related.
        </p>
      </motion.div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="flex flex-wrap justify-center gap-2 px-4"
      >
        {suggestions.map((text) => (
          <SuggestionPill key={text} text={text} onClick={onSuggestionClick} />
        ))}
      </motion.div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mt-8 text-center text-xs text-text-muted"
      >
        Answers are sourced from official McNeese pages
      </motion.p>
    </motion.div>
  );
}
