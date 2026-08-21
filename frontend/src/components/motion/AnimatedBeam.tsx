import { useReducedMotion } from "../../hooks/useReducedMotion";

interface AnimatedBeamProps {
  activeStep: number;
  steps: string[];
  className?: string;
}

/**
 * Adapted Magic UI AnimatedBeam — methodology path only.
 * Static SVG with active segment emphasis (no continuous neon loop).
 */
export function AnimatedBeam({ activeStep, steps, className = "" }: AnimatedBeamProps) {
  const reduced = useReducedMotion();
  const count = Math.max(steps.length, 1);

  return (
    <div className={`relative ${className}`} aria-hidden="true">
      <svg viewBox="0 0 320 360" className="h-full w-full" role="img">
        <title>Methodology path from ask through citation</title>
        {steps.map((label, index) => {
          const y = 40 + index * (280 / Math.max(count - 1, 1));
          const nextY = 40 + (index + 1) * (280 / Math.max(count - 1, 1));
          const active = index <= activeStep;
          return (
            <g key={label}>
              {index < count - 1 && (
                <line
                  x1="48"
                  y1={y + 14}
                  x2="48"
                  y2={nextY - 14}
                  stroke={active && index < activeStep ? "var(--brand-600)" : "var(--border-default)"}
                  strokeWidth={active && index < activeStep && !reduced ? 2.5 : 1.5}
                  strokeLinecap="round"
                />
              )}
              <circle
                cx="48"
                cy={y}
                r={index === activeStep ? 10 : 7}
                fill={active ? "var(--brand-700)" : "var(--surface)"}
                stroke={active ? "var(--brand-700)" : "var(--border-strong)"}
                strokeWidth="1.5"
              />
              <text
                x="78"
                y={y + 5}
                fontSize="14"
                fontFamily="var(--font-sans)"
                fill={index === activeStep ? "var(--text-primary)" : "var(--text-secondary)"}
                fontWeight={index === activeStep ? 600 : 450}
              >
                {label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
