import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Citation } from "../../types";
import "./citation-sources.css";

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
    if (
      (url.protocol === "http:" && url.port === "80") ||
      (url.protocol === "https:" && url.port === "443")
    ) {
      url.port = "";
    }
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

/** First letter of the registrable-ish label (mcneese.edu → M). */
export function domainInitial(url: string): string {
  const host = sourceHost(url);
  if (!host) return "?";
  const label = host.split(".")[0] || host;
  const letter = label.charAt(0);
  return letter ? letter.toUpperCase() : "?";
}

function readMobileSourcesMatch(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(max-width: 767px)").matches;
}

function useIsMobileSources(): boolean {
  const [isMobile, setIsMobile] = useState(readMobileSourcesMatch);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const media = window.matchMedia("(max-width: 767px)");
    const onChange = () => setIsMobile(media.matches);
    onChange();
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  return isMobile;
}

export function CitationGroup({ citations }: CitationGroupProps) {
  const uniqueCitations = useMemo(() => dedupeCitations(citations), [citations]);
  // Never auto-expand — keep the answer primary; user opens sources on demand.
  const [expanded, setExpanded] = useState(false);
  const isMobile = useIsMobileSources();

  if (!uniqueCitations || uniqueCitations.length === 0) return null;

  return (
    <div className="citationGroup">
      <button
        type="button"
        onClick={() => setExpanded((previous) => !previous)}
        className={
          isMobile
            ? "citationGroup__toggle citationGroup__toggle--mobile"
            : "citationGroup__toggle citationGroup__toggle--desktop inline-flex min-h-11 items-center gap-1.5 rounded-xl px-1 font-sans text-sm font-medium text-text-secondary transition-colors hover:text-text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
        }
        aria-expanded={expanded}
        aria-controls="citation-list"
        aria-label={`Sources used, ${uniqueCitations.length}`}
      >
        {isMobile ? (
          <>
            <span className="citationGroup__dotLine" aria-hidden="true">
            {uniqueCitations.slice(0, 5).map((citation, index) => (
              <span
                key={`${citation.id}-${index}`}
                className={
                  isOfficialMcNeese(citation.url)
                    ? "citationGroup__dot citationGroup__dot--official"
                    : "citationGroup__dot"
                }
                style={{ zIndex: uniqueCitations.length - index }}
              >
                {domainInitial(citation.url)}
              </span>
            ))}
            {uniqueCitations.length > 5 ? (
              <span className="citationGroup__dot citationGroup__dot--more">
                +{uniqueCitations.length - 5}
              </span>
            ) : null}
          </span>
            <span className="citationGroup__mobileLabel">
              {uniqueCitations.length} {uniqueCitations.length === 1 ? "source used" : "sources used"}
            </span>
          </>
        ) : (
          <span>Sources used · {uniqueCitations.length}</span>
        )}
        <motion.svg
          className="citationGroup__chevron h-3.5 w-3.5 shrink-0"
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
            <div className={isMobile ? "citationGroup__titleList" : "mt-2 space-y-1"}>
              {uniqueCitations.map((citation, index) =>
                isMobile ? (
                  <MobileTitleLink
                    key={`${citation.id}-${index}`}
                    citation={citation}
                    index={index + 1}
                  />
                ) : (
                  <CitationRow
                    key={`${citation.id}-${index}`}
                    citation={citation}
                    index={index + 1}
                  />
                ),
              )}
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

function isOfficialMcNeese(url: string): boolean {
  const host = sourceHost(url).toLowerCase();
  return host.endsWith("mcneese.edu");
}

function MobileTitleLink({ citation, index }: CitationRowProps) {
  return (
    <motion.a
      initial={{ opacity: 0, y: 3 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.02 }}
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className="citationGroup__titleLink"
    >
      <span className="citationGroup__titleText">{citation.title}</span>
      <span aria-hidden="true" className="citationGroup__titleArrow">
        ↗
      </span>
    </motion.a>
  );
}

function CitationRow({ citation, index }: CitationRowProps) {
  const host = sourceHost(citation.url);
  const official = isOfficialMcNeese(citation.url);
  const verifiedLive = citation.verifiedLive || citation.pageFetched;

  return (
    <motion.a
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`citationGroup__sourceRow${official ? " citationGroup__sourceRow--official" : ""}`}
    >
      <span className="citationGroup__sourceTitle">
        {citation.title}
      </span>
      <span className="citationGroup__sourceMeta">
        <span>
          {official ? "Official McNeese · " : "External · "}
          {verifiedLive ? "Page read live · " : ""}
          {host || "Open page"}
        </span>
        <span aria-hidden="true">↗</span>
      </span>
    </motion.a>
  );
}
