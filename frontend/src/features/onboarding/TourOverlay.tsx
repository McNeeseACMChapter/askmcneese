import {
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import type { TourStep } from "./tourSteps";

export interface SpotlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

interface TourOverlayProps {
  open: boolean;
  phase: "entering" | "active" | "exiting" | "route";
  step: TourStep;
  stepNumber: number;
  stepCount: number;
  isMobile: boolean;
  rect: SpotlightRect | null;
  interactiveTarget: boolean;
  drawerOpen: boolean;
  readingMode: boolean;
  subLabel?: string | null;
  showAck: boolean;
  targetMissing?: boolean;
  onAck: () => void;
  onRetryTarget?: () => void;
  onTargetClick: () => void;
}

type Placement = "center" | "dock-bottom" | "dock-top";

function padRect(rect: SpotlightRect, pad: number): SpotlightRect {
  return {
    top: Math.max(0, rect.top - pad),
    left: Math.max(0, rect.left - pad),
    width: Math.min(window.innerWidth - Math.max(0, rect.left - pad), rect.width + pad * 2),
    height: Math.min(window.innerHeight - Math.max(0, rect.top - pad), rect.height + pad * 2),
  };
}

function choosePlacement(rect: SpotlightRect | null, isMobile: boolean): Placement {
  if (!isMobile) return "center";
  if (!rect) return "dock-bottom";
  const mid = rect.top + rect.height / 2;
  return mid > window.innerHeight * 0.55 ? "dock-top" : "dock-bottom";
}

function annotateStyle(placement: Placement, isMobile: boolean): CSSProperties {
  const width = Math.min(isMobile ? 320 : 300, window.innerWidth - 40);
  if (placement === "center") {
    return { width };
  }
  if (placement === "dock-top") {
    return {
      top: "max(12px, env(safe-area-inset-top))",
      width,
    };
  }
  return {
    bottom: "max(16px, env(safe-area-inset-bottom))",
    width,
  };
}

function tetherPath(
  rect: SpotlightRect | null,
  box: DOMRect | null,
): { d: string; beadX: number; beadY: number } | null {
  if (!rect || !box) return null;

  const boxCx = box.left + box.width / 2;
  const boxCy = box.top + box.height / 2;
  const tCx = rect.left + rect.width / 2;
  const tCy = rect.top + rect.height / 2;

  const dx = tCx - boxCx;
  const dy = tCy - boxCy;
  const dist = Math.hypot(dx, dy);
  if (dist < 28) return null;

  const nx = dx / dist;
  const ny = dy / dist;
  const halfW = box.width / 2;
  const halfH = box.height / 2;
  const scale = Math.min(
    Math.abs(nx) > 1e-6 ? halfW / Math.abs(nx) : Number.POSITIVE_INFINITY,
    Math.abs(ny) > 1e-6 ? halfH / Math.abs(ny) : Number.POSITIVE_INFINITY,
  );
  const x1 = boxCx + nx * Math.max(8, scale - 2);
  const y1 = boxCy + ny * Math.max(8, scale - 2);

  const endPad = 12;
  const reach = Math.min(rect.width, rect.height) / 2 + endPad;
  const x2 = tCx - nx * reach;
  const y2 = tCy - ny * reach;

  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const bend = Math.min(80, dist * 0.3);
  const cx = mx - ny * bend;
  const cy = my + nx * bend;

  return {
    d: `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`,
    beadX: x2,
    beadY: y2,
  };
}

function arrowHeadPoints(x: number, y: number, target: SpotlightRect | null): string {
  if (!target) return `${x},${y} ${x - 5},${y - 4} ${x - 5},${y + 4}`;
  const tCx = target.left + target.width / 2;
  const tCy = target.top + target.height / 2;
  const angle = Math.atan2(tCy - y, tCx - x);
  const size = 7;
  const a1 = angle + Math.PI * 0.82;
  const a2 = angle - Math.PI * 0.82;
  return `${x},${y} ${x + Math.cos(a1) * size},${y + Math.sin(a1) * size} ${x + Math.cos(a2) * size},${y + Math.sin(a2) * size}`;
}

function useBoxRect(
  ref: RefObject<HTMLDivElement | null>,
  open: boolean,
  stepId: string,
  subLabel?: string | null,
): DOMRect | null {
  const [box, setBox] = useState<DOMRect | null>(null);

  useLayoutEffect(() => {
    if (!open) {
      setBox(null);
      return;
    }
    const measure = () => {
      const node = ref.current;
      if (!node) return;
      const next = node.getBoundingClientRect();
      setBox((prev) => {
        if (
          prev
          && Math.abs(prev.top - next.top) < 0.5
          && Math.abs(prev.left - next.left) < 0.5
          && Math.abs(prev.width - next.width) < 0.5
          && Math.abs(prev.height - next.height) < 0.5
        ) {
          return prev;
        }
        return next;
      });
    };
    const raf = window.requestAnimationFrame(measure);
    window.addEventListener("resize", measure);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", measure);
    };
  }, [open, ref, stepId, subLabel]);

  return box;
}

export function TourOverlay({
  open,
  phase,
  step,
  stepNumber,
  stepCount,
  isMobile,
  rect,
  interactiveTarget,
  drawerOpen,
  readingMode,
  subLabel,
  showAck,
  targetMissing,
  onAck,
  onRetryTarget,
  onTargetClick,
}: TourOverlayProps) {
  const reduceMotion = useReducedMotion();
  const titleId = useId();
  const descId = useId();
  const ctaRef = useRef<HTMLButtonElement>(null);
  const boxRef = useRef<HTMLDivElement>(null);
  const boxRect = useBoxRect(boxRef, open, step.id, subLabel);

  const pad = isMobile ? 7 : 8;
  const clear = rect && phase !== "route" ? padRect(rect, pad) : null;
  const placement = useMemo(
    () => choosePlacement(rect, isMobile || drawerOpen),
    [rect, isMobile, drawerOpen],
  );
  const style = useMemo(
    () => annotateStyle(placement, isMobile),
    [placement, isMobile],
  );

  const tether = useMemo(
    () => (readingMode || phase !== "active" || !clear ? null : tetherPath(clear, boxRect)),
    [clear, boxRect, readingMode, phase],
  );

  const scrims = useMemo(() => {
    if (!clear) {
      return [{ top: 0, left: 0, width: "100%", height: "100%" } as CSSProperties];
    }
    const { top, left, width, height } = clear;
    return [
      { top: 0, left: 0, width: "100%", height: top },
      { top: top + height, left: 0, width: "100%", height: Math.max(0, window.innerHeight - top - height) },
      { top, left: 0, width: left, height },
      { top, left: left + width, width: Math.max(0, window.innerWidth - left - width), height },
    ] satisfies CSSProperties[];
  }, [clear]);

  useEffect(() => {
    if (!open || !showAck) return;
    const timer = window.setTimeout(() => ctaRef.current?.focus(), 80);
    return () => window.clearTimeout(timer);
  }, [open, showAck, step.id, subLabel]);

  if (typeof document === "undefined") return null;

  const indexLabel = `${String(stepNumber).padStart(2, "0")} / ${String(stepCount).padStart(2, "0")}`;
  const dock = placement !== "center";
  const hideChrome = phase === "route" || phase === "exiting";

  return createPortal(
    <AnimatePresence>
      {open ? (
        <motion.div
          className={`tourRoot${readingMode ? " is-reading" : ""}${drawerOpen ? " is-drawer-open" : ""}`}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          aria-describedby={descId}
          data-phase={phase}
          initial={{ opacity: 0 }}
          animate={{ opacity: phase === "exiting" ? 0 : 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : phase === "exiting" ? 0.32 : 0.22 }}
        >
          {scrims.map((scrim, index) => (
            <div key={index} className="tourScrim" style={scrim} aria-hidden="true" />
          ))}

          {clear ? (
            <div
              className={`tourClearZone${interactiveTarget ? " is-interactive" : ""}`}
              style={{
                top: clear.top,
                left: clear.left,
                width: clear.width,
                height: clear.height,
              }}
              onClick={interactiveTarget ? onTargetClick : undefined}
              aria-hidden="true"
            >
              <div className="tourHalo" />
              <div className="tourCorners">
                <span className="tourCorner tl" />
                <span className="tourCorner tr" />
                <span className="tourCorner bl" />
                <span className="tourCorner br" />
              </div>
            </div>
          ) : null}

          {tether ? (
            <svg className="tourTether" width="100%" height="100%" aria-hidden="true">
              <path d={tether.d} />
              <polygon
                className="tourArrowHead"
                points={arrowHeadPoints(tether.beadX, tether.beadY, clear)}
              />
            </svg>
          ) : null}

          {!hideChrome ? (
            <div
              className={`tourAnnotateSlot${dock ? ` is-dock is-${placement}` : " is-center"}`}
              style={style}
            >
              <motion.div
                ref={boxRef}
                key={`${step.id}-${subLabel ?? ""}-${placement}`}
                className="tourAnnotate"
                initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.2 }}
              >
                <div className="tourProgress" aria-hidden="true">
                  <span style={{ width: `${(stepNumber / stepCount) * 100}%` }} />
                </div>
                <p className="tourStepIndex">Guided tour · {indexLabel}</p>
                {subLabel ? <p className="tourStepSub">{subLabel}</p> : null}
                <h2 id={titleId}>{step.title}</h2>
                <p id={descId}>{step.description}</p>
                {targetMissing ? (
                  <div className="tourActions">
                    <p className="tourHint">We couldn’t find this part of the interface.</p>
                    <button type="button" className="tourCta" onClick={onRetryTarget}>
                      Retry target →
                    </button>
                  </div>
                ) : (
                  <div className="tourActions">
                    {showAck ? (
                      <button
                        ref={ctaRef}
                        type="button"
                        className="tourCta"
                        onClick={onAck}
                      >
                        {step.nextLabel} →
                      </button>
                    ) : interactiveTarget ? (
                      <p className="tourHint">
                        {step.actionHint ?? "Use the highlighted control to continue."}
                      </p>
                    ) : readingMode ? (
                      <p className="tourHint">{step.actionHint ?? "Scroll to continue."}</p>
                    ) : step.actionHint ? (
                      <p className="tourHint">{step.actionHint}</p>
                    ) : null}
                  </div>
                )}
              </motion.div>
            </div>
          ) : null}

          <div className="tourLiveRegion" aria-live="polite">
            {`Step ${stepNumber} of ${stepCount}. ${step.title}. ${step.description}`}
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>,
    document.body,
  );
}
