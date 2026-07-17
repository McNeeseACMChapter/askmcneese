import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

interface AmbientSmokePulseProps {
  trigger: boolean | number | string;
  origin?: string;
  className?: string;
}

function usePrefersReducedEffects() {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
    return (
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
      window.matchMedia("(prefers-reduced-transparency: reduce)").matches
    );
  });

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const transparencyQuery = window.matchMedia("(prefers-reduced-transparency: reduce)");
    const update = () => setReduced(motionQuery.matches || transparencyQuery.matches);

    motionQuery.addEventListener("change", update);
    transparencyQuery.addEventListener("change", update);
    return () => {
      motionQuery.removeEventListener("change", update);
      transparencyQuery.removeEventListener("change", update);
    };
  }, []);

  return reduced;
}

export function AmbientSmokePulse({
  trigger,
  origin = "inset-0",
  className = "",
}: AmbientSmokePulseProps) {
  const reduced = usePrefersReducedEffects();
  const [pulseKey, setPulseKey] = useState(0);

  useEffect(() => {
    if (trigger === false) return;
    setPulseKey((current) => current + 1);
  }, [trigger]);

  if (reduced) return null;

  return (
    <div className={`pointer-events-none absolute ${origin} ${className}`} aria-hidden="true">
      <AnimatePresence>
        <motion.div
          key={pulseKey}
          initial={{ scale: 0.82, opacity: 0 }}
          animate={{ scale: 1.12, opacity: [0, 0.22, 0] }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="absolute left-1/2 top-1/2 h-56 w-56 -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            background:
              "radial-gradient(circle, color-mix(in srgb, var(--brand-600) 35%, transparent) 0%, color-mix(in srgb, var(--brand-900) 18%, transparent) 45%, transparent 72%)",
          }}
        />
      </AnimatePresence>
    </div>
  );
}
