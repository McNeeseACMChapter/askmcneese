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
  onSkip: () => void;
  onRetryTarget?: () => void;
  onTargetClick: () => void;
}

type Placement = "center" | "dock-bottom" | "dock-top" | "side-left" | "side-right";

function padRect(rect: SpotlightRect, pad: number): SpotlightRect {
  const left = Math.max(0, rect.left - pad);
  const top = Math.max(0, rect.top - pad);
  const right = Math.min(window.innerWidth, rect.left + rect.width + pad);
  const bottom = Math.min(window.innerHeight, rect.top + rect.height + pad);
  return {
    top,
    left,
    width: Math.max(0, right - left),
    height: Math.max(0, bottom - top),
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), Math.max(min, max));
}

export function annotationLayout(
  rect: SpotlightRect | null,
  isMobile: boolean,
  box: { height: number } | null,
): { placement: Placement; style: CSSProperties } {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const margin = isMobile ? 14 : 18;
  const gap = isMobile ? 18 : 24;
  const width = Math.min(isMobile ? 344 : 368, viewportWidth - margin * 2);
  const height = box?.height ?? (isMobile ? 210 : 200);

  if (!rect) {
    return {
      placement: "center",
      style: {
        top: clamp((viewportHeight - height) / 2, margin, viewportHeight - height - margin),
        left: clamp((viewportWidth - width) / 2, margin, viewportWidth - width - margin),
        width,
      },
    };
  }

  const targetCenterX = rect.left + rect.width / 2;
  const targetCenterY = rect.top + rect.height / 2;
  const above = rect.top - gap - margin;
  const below = viewportHeight - (rect.top + rect.height) - gap - margin;
  const leftSpace = rect.left - gap - margin;
  const rightSpace = viewportWidth - (rect.left + rect.width) - gap - margin;

  if (!isMobile && rightSpace >= width) {
    return {
      placement: "side-right",
      style: {
        top: clamp(targetCenterY - height / 2, margin, viewportHeight - height - margin),
        left: rect.left + rect.width + gap,
        width,
      },
    };
  }
  if (!isMobile && leftSpace >= width) {
    return {
      placement: "side-left",
      style: {
        top: clamp(targetCenterY - height / 2, margin, viewportHeight - height - margin),
        left: rect.left - gap - width,
        width,
      },
    };
  }
  if (below >= height) {
    return {
      placement: "dock-top",
      style: {
        top: rect.top + rect.height + gap,
        left: clamp(targetCenterX - width / 2, margin, viewportWidth - width - margin),
        width,
      },
    };
  }
  if (above >= height) {
    return {
      placement: "dock-bottom",
      style: {
        top: rect.top - gap - height,
        left: clamp(targetCenterX - width / 2, margin, viewportWidth - width - margin),
        width,
      },
    };
  }

  const placeAtTop = targetCenterY > viewportHeight / 2;
  return {
    placement: placeAtTop ? "dock-top" : "dock-bottom",
    style: {
      top: placeAtTop ? margin : Math.max(margin, viewportHeight - height - margin),
      left: clamp((viewportWidth - width) / 2, margin, viewportWidth - width - margin),
      width,
    },
  };
}

function rayBoundary(
  centerX: number,
  centerY: number,
  halfWidth: number,
  halfHeight: number,
  directionX: number,
  directionY: number,
): { x: number; y: number; scale: number } {
  const scaleX = Math.abs(directionX) > 1e-6
    ? halfWidth / Math.abs(directionX)
    : Number.POSITIVE_INFINITY;
  const scaleY = Math.abs(directionY) > 1e-6
    ? halfHeight / Math.abs(directionY)
    : Number.POSITIVE_INFINITY;
  const scale = Math.min(scaleX, scaleY);
  return {
    x: centerX + directionX * scale,
    y: centerY + directionY * scale,
    scale,
  };
}

export function tetherPath(
  rect: SpotlightRect | null,
  box: DOMRect | null,
): { d: string; beadX: number; beadY: number } | null {
  if (!rect || !box) return null;
  const boxRight = box.left + box.width;
  const boxBottom = box.top + box.height;
  const targetRight = rect.left + rect.width;
  const targetBottom = rect.top + rect.height;
  const separated = boxRight < rect.left || box.left > targetRight
    || boxBottom < rect.top || box.top > targetBottom;
  if (!separated) return null;

  const boxCx = box.left + box.width / 2;
  const boxCy = box.top + box.height / 2;
  const targetCx = rect.left + rect.width / 2;
  const targetCy = rect.top + rect.height / 2;
  const dx = targetCx - boxCx;
  const dy = targetCy - boxCy;
  const distance = Math.hypot(dx, dy);
  if (distance < 34) return null;

  const nx = dx / distance;
  const ny = dy / distance;
  const start = rayBoundary(boxCx, boxCy, box.width / 2, box.height / 2, nx, ny);
  const startX = start.x + nx * 2;
  const startY = start.y + ny * 2;
  const targetBoundary = rayBoundary(
    targetCx,
    targetCy,
    rect.width / 2,
    rect.height / 2,
    -nx,
    -ny,
  );
  const endX = targetBoundary.x - nx * 7;
  const endY = targetBoundary.y - ny * 7;

  return {
    d: "M " + startX + " " + startY + " L " + endX + " " + endY,
    beadX: endX,
    beadY: endY,
  };
}

function arrowHeadPoints(x: number, y: number, target: SpotlightRect | null): string {
  if (!target) return [x + "," + y, (x - 5) + "," + (y - 4), (x - 5) + "," + (y + 4)].join(" ");
  const targetCx = target.left + target.width / 2;
  const targetCy = target.top + target.height / 2;
  const angle = Math.atan2(targetCy - y, targetCx - x);
  const size = 7;
  const a1 = angle + Math.PI * 0.82;
  const a2 = angle - Math.PI * 0.82;
  return [
    x + "," + y,
    (x + Math.cos(a1) * size) + "," + (y + Math.sin(a1) * size),
    (x + Math.cos(a2) * size) + "," + (y + Math.sin(a2) * size),
  ].join(" ");
}
interface MeasuredSize {
  width: number;
  height: number;
}

function useBoxSize(
  ref: RefObject<HTMLDivElement | null>,
  open: boolean,
  stepId: string,
  subLabel?: string | null,
): MeasuredSize | null {
  const [size, setSize] = useState<MeasuredSize | null>(null);

  useLayoutEffect(() => {
    if (!open) {
      setSize(null);
      return;
    }
    const measure = () => {
      const node = ref.current;
      if (!node) return;
      const next = node.getBoundingClientRect();
      setSize((previous) => {
        if (
          previous
          && Math.abs(previous.width - next.width) < 0.5
          && Math.abs(previous.height - next.height) < 0.5
        ) return previous;
        return { width: next.width, height: next.height };
      });
    };
    const raf = window.requestAnimationFrame(measure);
    const observer = new ResizeObserver(measure);
    if (ref.current) observer.observe(ref.current);
    window.addEventListener("resize", measure);
    return () => {
      window.cancelAnimationFrame(raf);
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [open, ref, stepId, subLabel]);

  return size;
}

function rectFromLayout(
  style: CSSProperties,
  size: MeasuredSize | null,
  isMobile: boolean,
): DOMRect {
  const left = Number(style.left ?? 0);
  const top = Number(style.top ?? 0);
  const width = Number(style.width ?? size?.width ?? (isMobile ? 344 : 368));
  const height = size?.height ?? (isMobile ? 210 : 200);
  return {
    x: left,
    y: top,
    left,
    top,
    width,
    height,
    right: left + width,
    bottom: top + height,
    toJSON: () => ({ left, top, width, height }),
  } as DOMRect;
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
  onSkip,
  onRetryTarget,
  onTargetClick,
}: TourOverlayProps) {
  const reduceMotion = useReducedMotion();
  const titleId = useId();
  const descId = useId();
  const ctaRef = useRef<HTMLButtonElement>(null);
  const boxRef = useRef<HTMLDivElement>(null);
  const boxSize = useBoxSize(boxRef, open, step.id, subLabel);

  const pad = isMobile ? 7 : 8;
  const clear = rect && phase !== "route" ? padRect(rect, pad) : null;
  const layout = useMemo(
    () => annotationLayout(clear, isMobile || drawerOpen, boxSize),
    [boxSize, clear, drawerOpen, isMobile],
  );
  const placement = layout.placement;
  const style = layout.style;
  const placedBoxRect = useMemo(
    () => rectFromLayout(style, boxSize, isMobile || drawerOpen),
    [boxSize, drawerOpen, isMobile, style.left, style.top, style.width],
  );

  const tether = useMemo(
    () => (readingMode || phase !== "active" || !clear ? null : tetherPath(clear, placedBoxRect)),
    [clear, placedBoxRect, readingMode, phase],
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
              <path className="tourTetherUnderlay" d={tether.d} />
              <path className="tourTetherLine" d={tether.d} />
              <circle className="tourTetherTarget" cx={tether.beadX} cy={tether.beadY} r="7" />
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
                <div className="tourTopline">
                  <p className="tourStepIndex">Guided tour · {indexLabel}</p>
                  <button type="button" className="tourSkip" onClick={onSkip}>
                    Skip walkthrough
                  </button>
                </div>
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
