import { motion } from "framer-motion";
import { scaleIn } from "../../lib/motion";
import type { Citation } from "../../types";

interface CitationCardProps {
  citation: Citation;
}

export function CitationCard({ citation }: CitationCardProps) {
  return (
    <motion.a
      variants={scaleIn}
      initial="hidden"
      animate="visible"
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-start gap-2 rounded-lg border border-border bg-gray-50/50 p-2.5 transition-all hover:border-mcneese-blue/30 hover:bg-mcneese-blue/5 hover:shadow-soft"
    >
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-mcneese-blue/10 text-mcneese-blue transition-colors group-hover:bg-mcneese-blue group-hover:text-white">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <p className="answerSourceTitle truncate group-hover:text-mcneese-blue">{citation.title}</p>
        {citation.snippet && (
          <p className="answerCardDescription line-clamp-2">{citation.snippet}</p>
        )}
        <p className="answerSourceDetail mt-1 flex items-center gap-1 text-mcneese-blue">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
          <span className="truncate">{new URL(citation.url).hostname}</span>
        </p>
      </div>
    </motion.a>
  );
}
