import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Citation } from "../../types";

interface CitationGroupProps {
  citations: Citation[];
}

export function CitationGroup({ citations }: CitationGroupProps) {
  const [expanded, setExpanded] = useState(false);

  // Dedupe citations by title
  const uniqueCitations = useMemo(() => {
    const seen = new Set<string>();
    return citations.filter((c) => {
      const key = c.title.toLowerCase().trim();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [citations]);

  if (!uniqueCitations || uniqueCitations.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-mcneese-blue/30 rounded px-1 -mx-1"
        aria-expanded={expanded}
        aria-controls="citation-list"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>{uniqueCitations.length} source{uniqueCitations.length !== 1 ? "s" : ""}</span>
        <motion.svg
          className="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </motion.svg>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            id="citation-list"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-0.5">
              {uniqueCitations.map((citation, index) => (
                <CitationRow key={`${citation.id}-${index}`} citation={citation} index={index + 1} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface CitationRowProps {
  citation: Citation;
  index: number;
}

function CitationRow({ citation, index }: CitationRowProps) {
  return (
    <motion.a
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-bg-secondary transition-colors group"
    >
      <span className="flex h-5 w-5 items-center justify-center rounded bg-primary-subtle text-[10px] font-semibold text-mcneese-blue flex-shrink-0">
        {index}
      </span>
      <span className="flex-1 truncate text-text-secondary group-hover:text-mcneese-blue transition-colors">
        {citation.title}
      </span>
      <svg 
        className="h-3 w-3 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor" 
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </motion.a>
  );
}
