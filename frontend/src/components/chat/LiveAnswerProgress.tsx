import { memo, useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Check, ChevronDown, CircleAlert, Square } from "lucide-react";
import type { AskRun, LiveStage } from "../../lib/askRun";
import { phaseForEvent, shouldShowLiveActivity } from "../../lib/askRun";
import {
  buildResearchNarration,
  timeoutFallbackDetail,
  type ResearchEvidence,
  type ResearchHistoryRow,
  type ResearchNarration,
} from "../../lib/researchPresentation";
import { AppIcon } from "../ui/AppIcon";

interface LiveAnswerProgressProps {
  run: AskRun;
}

const swap = { duration: 0.2, ease: [0.22, 1, 0.36, 1] as const };
const rise = { duration: 0.18, ease: [0.22, 1, 0.36, 1] as const };

export const LiveAnswerProgress = memo(function LiveAnswerProgress({
  run,
}: LiveAnswerProgressProps) {
  const reduceMotion = Boolean(useReducedMotion());
  const detailsId = useId();
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [showEarlier, setShowEarlier] = useState(false);
  const [tick, setTick] = useState(0);
  const [statusText, setStatusText] = useState("");
  const lastAnnounceKey = useRef("");
  const lastEventAtRef = useRef(Date.now());
  const lastStageCountRef = useRef(0);

  const active =
    run.status === "queued" || run.status === "running" || run.status === "streaming";
  const visible = shouldShowLiveActivity(run);
  const narration = visible ? buildResearchNarration(run) : null;

  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setTick((n) => n + 1), 500);
    return () => window.clearInterval(timer);
  }, [active, run.runId]);

  useEffect(() => {
    if (run.stages.length !== lastStageCountRef.current) {
      lastStageCountRef.current = run.stages.length;
      lastEventAtRef.current = Date.now();
    }
  }, [run.stages.length]);

  useEffect(() => {
    if (!active) {
      setDetailsOpen(false);
      setShowEarlier(false);
    }
  }, [active]);

  useEffect(() => {
    if (!narration || narration.result !== "active") return;
    if (narration.announceKey === lastAnnounceKey.current) return;
    lastAnnounceKey.current = narration.announceKey;
    setStatusText(narration.announceText);
  }, [narration]);

  void tick;

  if (!visible || !narration) return null;

  const quietMs = Date.now() - lastEventAtRef.current;
  const fallbackDetail = timeoutFallbackDetail(
    narration,
    quietMs,
    run.stages.length > 0,
  );
  const detail = fallbackDetail ?? narration.currentDetail;

  if (narration.result !== "active") {
    return (
      <CompletedTrail
        narration={narration}
        run={run}
        detailsId={detailsId}
        detailsOpen={detailsOpen}
        onToggle={() => setDetailsOpen((o) => !o)}
        reduceMotion={reduceMotion}
      />
    );
  }

  const isMobile =
    typeof window !== "undefined" && window.matchMedia("(max-width: 640px)").matches;
  const evidence = narration.evidence.slice(-(isMobile ? 1 : 2));
  const historyRows = showEarlier ? narration.history : narration.history.slice(-3);

  return (
    <section
      className="researchTrail"
      data-compact={narration.compact || undefined}
      data-testid="research-trail"
      aria-label="Live research activity"
      aria-busy="true"
    >
      <div className="researchTrailCurrent">
        <StatusGlyph
          active
          tone={narration.compact ? "write" : "live"}
          reduceMotion={reduceMotion}
        />
        <div className="researchTrailCurrentBody" aria-hidden="true">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={narration.announceKey + (detail ?? "")}
              className="researchTrailCurrentContent"
              initial={reduceMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -6 }}
              transition={reduceMotion ? { duration: 0 } : swap}
            >
              <p className="researchTrailCurrentLabel">{narration.currentLabel}</p>
              {detail ? <p className="researchTrailCurrentDetail">{detail}</p> : null}
            </motion.div>
          </AnimatePresence>
        </div>
        {narration.elapsed ? (
          <span className="researchTrailElapsed">{narration.elapsed}</span>
        ) : null}
        {(narration.history.length > 0 || run.stages.length > 1) && (
          <button
            type="button"
            className="researchTrailDetailsButton"
            aria-expanded={detailsOpen}
            aria-controls={detailsId}
            aria-label={detailsOpen ? "Hide activity" : "View activity"}
            onClick={() => setDetailsOpen((o) => !o)}
          >
            <span>{detailsOpen ? "Hide" : "Details"}</span>
            <AppIcon icon={ChevronDown} size={14} />
          </button>
        )}
      </div>

      {!narration.compact && evidence.length > 0 ? (
        <ul className="researchTrailSources" aria-hidden="true">
          <AnimatePresence initial={false}>
            {evidence.map((item, index) => (
              <motion.li
                key={item.id}
                className="researchTrailSource"
                data-subdued={index !== evidence.length - 1 || undefined}
                initial={reduceMotion ? false : { opacity: 0, y: 5 }}
                animate={{ opacity: index !== evidence.length - 1 ? 0.6 : 1, y: 0 }}
                exit={reduceMotion ? undefined : { opacity: 0 }}
                transition={reduceMotion ? { duration: 0 } : rise}
              >
                <EvidenceLink item={item} />
                {item.host ? (
                  <span className="researchTrailSourceHost">{item.host}</span>
                ) : null}
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      ) : null}

      {detailsOpen ? (
        <div id={detailsId}>
          {historyRows.length > 0 ? (
            <ul className="researchTrailHistory">
              {historyRows.map((row) => (
                <HistoryRow key={row.id} row={row} />
              ))}
            </ul>
          ) : null}
          {narration.earlierCount > 0 && !showEarlier ? (
            <button
              type="button"
              className="researchTrailEarlier"
              onClick={() => setShowEarlier(true)}
            >
              Earlier activity ({narration.earlierCount})
            </button>
          ) : null}
        </div>
      ) : null}

      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {statusText}
      </p>
    </section>
  );
});

function StatusGlyph({
  active,
  tone = "live",
  result,
  reduceMotion,
}: {
  active?: boolean;
  /** McNeese signal: blue while researching, gold while writing. */
  tone?: "live" | "write";
  result?: ResearchNarration["result"];
  reduceMotion: boolean;
}) {
  if (result === "failed") {
    return (
      <span className="researchTrailGlyph researchTrailGlyphFail" aria-hidden="true">
        <AppIcon icon={CircleAlert} size={12} />
      </span>
    );
  }
  if (result === "cancelled") {
    return (
      <span className="researchTrailGlyph researchTrailGlyphStop" aria-hidden="true">
        <AppIcon icon={Square} size={10} />
      </span>
    );
  }
  if (!active) {
    return (
      <span className="researchTrailGlyph researchTrailGlyphCheck" aria-hidden="true">
        <AppIcon icon={Check} size={12} />
      </span>
    );
  }
  return (
    <span
      className="researchTrailGlyph"
      data-tone={tone}
      aria-hidden="true"
    >
      {!reduceMotion ? (
        <>
          <span className="researchTrailGlyphRing" />
          <span className="researchTrailGlyphRing researchTrailGlyphRing--late" />
        </>
      ) : null}
      <span className="researchTrailGlyphCore" />
    </span>
  );
}

function EvidenceLink({ item }: { item: ResearchEvidence }) {
  if (item.url) {
    return (
      <a
        className="researchTrailSourceTitle"
        href={item.url}
        target="_blank"
        rel="noreferrer"
        title={item.title}
      >
        {item.title}
      </a>
    );
  }
  return <p className="researchTrailSourceTitle">{item.title}</p>;
}

function HistoryRow({ row }: { row: ResearchHistoryRow }) {
  return (
    <li className="researchTrailHistoryRow" data-status={row.status}>
      <span className="researchTrailHistoryMark" aria-hidden="true">
        {row.status === "failed" ? (
          <AppIcon icon={CircleAlert} size={11} />
        ) : row.status === "cancelled" ? (
          <AppIcon icon={Square} size={9} />
        ) : (
          <AppIcon icon={Check} size={11} />
        )}
      </span>
      <span>{row.label}</span>
    </li>
  );
}

function CompletedTrail({
  narration,
  run,
  detailsId,
  detailsOpen,
  onToggle,
  reduceMotion,
}: {
  narration: ResearchNarration;
  run: AskRun;
  detailsId: string;
  detailsOpen: boolean;
  onToggle: () => void;
  reduceMotion: boolean;
}) {
  const title = `${narration.completedTitle}${
    narration.elapsed ? ` · ${narration.elapsed}` : ""
  }`;

  const history = run.stages
    .filter((s) => s.status !== "active" && s.kind !== "evidence")
    .slice(-6)
    .map(
      (s): ResearchHistoryRow => ({
        id: s.id,
        label: s.label,
        status:
          s.status === "failed"
            ? "failed"
            : s.status === "cancelled"
              ? "cancelled"
              : "completed",
      }),
    );

  return (
    <section
      className="researchTrail researchTrail--settled"
      data-result={narration.result}
      data-testid="research-trail-completed"
      aria-label="Completed research activity"
    >
      <div className="researchTrailCompleted">
        <StatusGlyph result={narration.result} reduceMotion={reduceMotion} />
        <span className="researchTrailCompletedTitle">{title}</span>
        {history.length > 0 ? (
          <button
            type="button"
            className="researchTrailDetailsButton"
            aria-expanded={detailsOpen}
            aria-controls={detailsId}
            onClick={onToggle}
          >
            <span>{detailsOpen ? "Hide" : "View activity"}</span>
            <AppIcon icon={ChevronDown} size={14} />
          </button>
        ) : null}
      </div>
      {detailsOpen ? (
        <ul id={detailsId} className="researchTrailHistory">
          {history.map((row) => (
            <HistoryRow key={row.id} row={row} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}

/** Rebuild a display run from a persisted message summary. */
export function runFromMessageSummary(
  assistantMessageId: string,
  summary: NonNullable<import("../../types").ChatMessage["runSummary"]>,
): AskRun {
  const persistedStages = summary.stages as Array<
    (typeof summary.stages)[number] & Partial<LiveStage>
  >;
  const duration = summary.durationMs ?? 0;
  const completedAt = Date.now();

  return {
    runId: summary.runId,
    requestId: summary.runId,
    turnId: summary.runId,
    userMessageId: "",
    assistantMessageId,
    status: summary.status,
    startedAt: completedAt - duration,
    completedAt,
    stages: persistedStages.map((stage, index) => ({
      ...stage,
      phase: stage.phase ?? phaseForEvent(stage.event),
      kind: stage.kind ?? "milestone",
      status: stage.status === "active" ? "cancelled" : stage.status,
      sequence: index,
    })) as LiveStage[],
    processedEventKeys: [],
    sourcesFound: summary.sourcesFound,
    sourcesRead: summary.sourcesRead,
    citationsUsed: summary.citationsUsed,
  };
}
