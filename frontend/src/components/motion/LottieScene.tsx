/**
 * Lottie wrapper reserved for approved local JSON assets.
 * No public/random Lottie is embedded. Methodology uses static SVG until approved.
 */
import { useEffect, useRef } from "react";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface LottieSceneProps {
  /** Local JSON path under /public or imported module — required for playback */
  animationData?: object | null;
  className?: string;
  label: string;
  play?: boolean;
}

export function LottieScene({ animationData = null, className = "", label, play = true }: LottieSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (!animationData || reduced || !play) return;
    let destroyed = false;
    let instance: { destroy: () => void } | null = null;

    (async () => {
      const lottie = await import("lottie-web");
      if (destroyed || !containerRef.current) return;
      instance = lottie.default.loadAnimation({
        container: containerRef.current,
        renderer: "svg",
        loop: false,
        autoplay: true,
        animationData,
      });
    })();

    return () => {
      destroyed = true;
      instance?.destroy();
    };
  }, [animationData, reduced, play]);

  if (!animationData) {
    return (
      <div className={className} role="img" aria-label={label}>
        <p className="text-sm text-text-muted">
          Motion illustration unavailable — approved Lottie asset not provided.
        </p>
      </div>
    );
  }

  if (reduced) {
    return (
      <div className={className} role="img" aria-label={label}>
        <p className="text-sm text-text-secondary">{label}</p>
      </div>
    );
  }

  return <div ref={containerRef} className={className} role="img" aria-label={label} />;
}
