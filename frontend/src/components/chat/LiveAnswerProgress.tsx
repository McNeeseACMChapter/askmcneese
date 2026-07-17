import { memo, useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Check, CircleAlert } from "lucide-react";
import type { AskRun, LiveStage } from "../../lib/askRun";
import {
  completedRunHeadline,
  formatRunElapsed,
  shouldShowLiveActivity,
  visibleStages,
} from "../../lib/askRun";
import { AppIcon } from "../ui/AppIcon";

interface LiveAnswerProgressProps {
  run: AskRun;
}

const motionTokens = {
  panelEnter: { duration: 0.22, ease: [0.22, 1, 0.36, 1] as const },
  stageEnter: { duration: 0.18, ease: "easeOut" as const },
  collapse: { duration: 0.24, ease: [0.22, 1, 0.36, 1] as const },
  /** Status line enters from the right and exits left with fade */
  statusSwap: { duration: 0.28, ease: [0.22, 1, 0.36, 1] as const },
};

function currentLiveLine(run: AskRun): { key: string; text: string; step: number } {
  if (run.stages.length === 0) {
    return { key: `${run.runId}-starting`, text: "Starting…", step: 1 };
  }
  const active = [...run.stages].reverse().find((s) => s.status === "active");
  const stage = active ?? run.stages[run.stages.length - 1];
  const detail = stage.detail ? ` · ${stage.detail}` : "";
  return {
    key: stage.id,
    text: `${stage.label}${detail}`,
    step: stage.sequence + 1,
  };
}

/**
 * Turn-owned live activity panel.
 * Header: step counter + “Live:” + status line that slides RTL on each event.
 */
export const LiveAnswerProgress = memo(function LiveAnswerProgress({
  run,
}: LiveAnswerProgressProps) {
  const reduceMotion = useReducedMotion();
  const active =
    run.status === "queued" || run.status === "running" || run.status === "streaming";
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!active) return;
    const id = window.setInterval(() => setTick((n) => n + 1), 1000);
    return () => window.clearInterval(id);
  }, [active, run.runId]);

  useEffect(() => {
    if (!active) setDetailsOpen(false);
  }, [active]);

  if (!shouldShowLiveActivity(run)) return null;

  const elapsed = formatRunElapsed(run);
  void tick;
  const { hiddenCount, stages } = visibleStages(run, active ? 4 : 6);
  const sources = run.sourcesFound;
  const line = currentLiveLine(run);

  if (!active) {
    return (
      <CompletedRunSummary
        run={run}
        elapsed={elapsed}
        stages={run.stages}
        detailsOpen={detailsOpen}
        onToggleDetails={() => setDetailsOpen((v) => !v)}
        reduceMotion={Boolean(reduceMotion)}
      />
    );
  }

  return (
    <motion.section
      className="live-activity w-full max-w-[var(--chat-assistant-max)]"
      aria-label="Live answer activity"
      aria-live="polite"
      aria-busy="true"
      initial={reduceMotion ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={reduceMotion ? { duration: 0 } : motionTokens.panelEnter}
    >
      <header className="live-activity-header">
        <span className="live-activity-lead" aria-hidden="true">
          <span className="live-activity-counter">{line.step}</span>
          <span className="live-activity-live">Live</span>
          <span className="live-activity-colon">:</span>
        </span>
        <span className="live-activity-status-slot">
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={line.key}
              className="live-activity-status"
              initial={reduceMotion ? false : { opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, x: -14 }}
              transition={reduceMotion ? { duration: 0 } : motionTokens.statusSwap}
            >
              {line.text}
            </motion.span>
          </AnimatePresence>
        </span>
        {elapsed ? <span className="live-activity-elapsed">{elapsed}</span> : null}
      </header>

      {/* Screen-reader friendly full line (visible ticker is decorative for SR) */}
      <span className="sr-only">
        Live step {line.step}: {line.text}
      </span>

      {hiddenCount > 0 && (
        <button
          type="button"
          className="live-activity-more"
          onClick={() => setDetailsOpen((v) => !v)}
          aria-expanded={detailsOpen}
        >
          {detailsOpen ? "Hide earlier activity" : `View ${hiddenCount} earlier steps`}
        </button>
      )}

      <ol className="live-activity-list" aria-label="Current answer activity">
        <AnimatePresence initial={false}>
          {(detailsOpen ? run.stages : stages).length === 0 ? (
            <ActivityRow
              key={`${run.runId}-starting`}
              stage={{
                id: `${run.runId}-starting`,
                event: "request.accepted",
                label: "Starting…",
                status: "active",
                sequence: 0,
              }}
              isCurrent
              reduceMotion={Boolean(reduceMotion)}
            />
          ) : (
            (detailsOpen ? run.stages : stages).map((stage) => (
              <ActivityRow
                key={stage.id}
                stage={stage}
                isCurrent={stage.status === "active"}
                reduceMotion={Boolean(reduceMotion)}
              />
            ))
          )}
        </AnimatePresence>
      </ol>

      {typeof sources === "number" && sources > 0 && (
        <p className="live-activity-meta">
          {sources} source{sources === 1 ? "" : "s"} reviewed
        </p>
      )}
    </motion.section>
  );
});

const ActivityRow = memo(function ActivityRow({
  stage,
  isCurrent,
  reduceMotion,
}: {
  stage: LiveStage;
  isCurrent: boolean;
  reduceMotion: boolean;
}) {
  return (
    <motion.li
      {...(reduceMotion ? {} : { layout: true })}
      initial={reduceMotion || !isCurrent ? false : { opacity: 0, x: 12 }}
      animate={{ opacity: isCurrent ? 1 : 0.72, x: 0 }}
      exit={reduceMotion ? undefined : { opacity: 0, x: -8 }}
      transition={reduceMotion ? { duration: 0 } : motionTokens.stageEnter}
      className={`live-activity-row${isCurrent ? " is-current" : ""}${
        stage.status === "failed" ? " is-failed" : ""
      }`}
    >
      <span className="live-activity-marker" aria-hidden="true">
        {stage.status === "failed" ? "!" : stage.status === "completed" ? "✓" : "·"}
      </span>
      <span className="live-activity-label">
        {stage.label}
        {stage.detail ? (
          <span className="live-activity-detail"> · {stage.detail}</span>
        ) : null}
      </span>
    </motion.li>
  );
});

function CompletedRunSummary({
  run,
  elapsed,
  stages,
  detailsOpen,
  onToggleDetails,
  reduceMotion,
}: {
  run: AskRun;
  elapsed: string | null;
  stages: LiveStage[];
  detailsOpen: boolean;
  onToggleDetails: () => void;
  reduceMotion: boolean;
}) {
  const failed = run.status === "failed" || run.status === "cancelled";
  const title = completedRunHeadline(run);
  const stepCount = stages.length;

  return (
    <section className="live-activity live-activity-completed" aria-label="Completed answer activity">
      <header className="live-activity-header">
        <span className="live-activity-lead">
          <span className="live-activity-done-icon" aria-hidden="true">
            <AppIcon icon={failed ? CircleAlert : Check} size={14} />
          </span>
          <span className="live-activity-title">{title}</span>
          {stepCount > 0 ? (
            <span className="live-activity-step-total">{stepCount} steps</span>
          ) : null}
        </span>
        {elapsed && <span className="live-activity-elapsed">{elapsed}</span>}
        {stages.length > 0 && (
          <button
            type="button"
            className="live-activity-more"
            onClick={onToggleDetails}
            aria-expanded={detailsOpen}
          >
            {detailsOpen ? "Hide activity" : "View activity"}
          </button>
        )}
      </header>
      <AnimatePresence initial={false}>
        {detailsOpen && (
          <motion.ol
            className="live-activity-list"
            initial={reduceMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
            transition={reduceMotion ? { duration: 0 } : motionTokens.collapse}
          >
            {stages.map((stage) => (
              <li key={stage.id} className="live-activity-row">
                <span className="live-activity-marker" aria-hidden="true">
                  {stage.status === "failed" ? "!" : "✓"}
                </span>
                <span className="live-activity-label">
                  {stage.label}
                  {stage.detail ? (
                    <span className="live-activity-detail"> · {stage.detail}</span>
                  ) : null}
                </span>
              </li>
            ))}
          </motion.ol>
        )}
      </AnimatePresence>
    </section>
  );
}

/** Convenience: build a display AskRun from a persisted message runSummary. */
export function runFromMessageSummary(
  assistantMessageId: string,
  summary: NonNullable<import("../../types").ChatMessage["runSummary"]>,
): AskRun {
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
    stages: summary.stages.map((stage, index) => ({
      ...stage,
      // Interrupted/incomplete rows never re-enter "active" after reload.
      status: stage.status === "active" ? "failed" : stage.status,
      sequence: index,
    })),
    processedEventKeys: [],
    sourcesFound: summary.sourcesFound,
  };
}
