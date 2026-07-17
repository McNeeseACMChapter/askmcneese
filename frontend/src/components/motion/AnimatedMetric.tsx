import { useEffect, useRef, useState } from "react";
import { animate, useMotionValue, useMotionValueEvent } from "framer-motion";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface AnimatedMetricProps {
  value: number | null | undefined;
  format?: (value: number) => string;
  className?: string;
  suffix?: string;
}

/** Animates real metric changes only — never restarts from zero on mount unless previous was undefined. */
export function AnimatedMetric({
  value,
  format = (n) => String(Math.round(n)),
  className = "",
  suffix = "",
}: AnimatedMetricProps) {
  const reduced = useReducedMotion();
  const previous = useRef<number | null>(null);
  const motionValue = useMotionValue(typeof value === "number" ? value : 0);
  const [display, setDisplay] = useState(() =>
    typeof value === "number" ? `${format(value)}${suffix}` : "—",
  );
  const [announced, setAnnounced] = useState(() =>
    typeof value === "number" ? `${format(value)}${suffix}` : "—",
  );

  useMotionValueEvent(motionValue, "change", (latest) => {
    setDisplay(`${format(latest)}${suffix}`);
  });

  useEffect(() => {
    if (typeof value !== "number" || Number.isNaN(value)) {
      setDisplay("—");
      setAnnounced("—");
      return;
    }
    const formatted = `${format(value)}${suffix}`;
    const from = previous.current ?? value;
    previous.current = value;
    if (reduced || from === value) {
      motionValue.set(value);
      setDisplay(formatted);
      setAnnounced(formatted);
      return;
    }
    const controls = animate(from, value, {
      duration: 0.55,
      ease: [0.2, 0, 0, 1],
      onUpdate: (latest) => motionValue.set(latest),
      onComplete: () => setAnnounced(formatted),
    });
    return () => controls.stop();
  }, [value, reduced, format, suffix, motionValue]);

  return (
    <span className={className} aria-label={announced}>
      <span aria-hidden="true">{display}</span>
    </span>
  );
}
