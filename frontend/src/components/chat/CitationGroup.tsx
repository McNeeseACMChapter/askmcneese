import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Citation } from "../../types";

interface CitationGroupProps {
  citations: Citation[];
}

/** Normalize citation URLs for identity comparison. Never throws. */
export function normalizeCitationUrl(raw: string | undefined | null): string | null {
  if (typeof raw !== "string") return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  try {
    const url = new URL(trimmed);
    url.hash = "";
    url.protocol = url.protocol.toLowerCase();
    url.hostname = url.hostname.toLowerCase();
    // Drop default ports
    if (
      (url.protocol === "http:" && url.port === "80") ||
      (url.protocol === "https:" && url.port === "443")
    ) {
      url.port = "";
    }
    // Remove trailing slash on non-root paths only
    if (url.pathname.length > 1 && url.pathname.endsWith("/")) {
      url.pathname = url.pathname.replace(/\/+$/, "");
    }
    return url.toString();
  } catch {
    return null;
  }
}

export function citationDedupeKey(citation: Citation): string {
  const normalized = normalizeCitationUrl(citation.url);
  if (normalized) return `url:${normalized}`;
  const title = (citation.title ?? "").trim().toLowerCase();
  const rawUrl = (citation.url ?? "").trim().toLowerCase();
  if (title || rawUrl) return `fallback:${title}|${rawUrl}`;
  return `fallback:id:${citation.id ?? ""}`;
}

export function dedupeCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  const result: Citation[] = [];
  for (const citation of citations) {
    const key = citationDedupeKey(citation);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(citation);
  }
  return result;
}

function sourceHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export function CitationGroup({ citations }: CitationGroupProps) {
  const uniqueCitations = useMemo(() => dedupeCitations(citations), [citations]);
  // Expand by default for ≤3 sources; collapse when many to keep the answer primary.
  const [expanded, setExpanded] = useState(
    () => uniqueCitations.length > 0 && uniqueCitations.length <= 3,
  );

  if (!uniqueCitations || uniqueCitations.length === 0) return null;

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="inline-flex min-h-11 items-center gap-1.5 rounded-xl px-1 font-sans text-sm font-medium text-text-secondary transition-colors hover:text-text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
        aria-expanded={expanded}
        aria-controls="citation-list"
      >
        <span>Sources · {uniqueCitations.length}</span>
        <motion.svg
          className="h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.75}
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          aria-hidden
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
            <div className="mt-2 space-y-1">
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
  const host = sourceHost(citation.url);
  const snippet = citation.snippet?.trim();

  return (
    <motion.a
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-xl px-2 py-2.5 transition-colors hover:bg-brand-50/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
    >
      <span className="block font-sans text-sm font-medium text-text-primary">{citation.title}</span>
      {snippet ? (
        <span className="mt-1 block font-sans text-xs leading-snug text-text-secondary line-clamp-2">
          {snippet}
        </span>
      ) : null}
      <span className="mt-1.5 flex items-center gap-1.5 font-sans text-xs text-brand-700">
        <span>{host || "Open page"}</span>
        <span aria-hidden="true">↗</span>
      </span>
    </motion.a>
  );
}
