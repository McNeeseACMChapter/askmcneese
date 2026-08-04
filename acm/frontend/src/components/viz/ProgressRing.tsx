interface ProgressRingProps {
  value: number;
  label: string;
  size?: number;
}

export function ProgressRing({ value, label, size = 56 }: ProgressRingProps) {
  const v = Math.max(0, Math.min(100, value));
  const stroke = 5;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (v / 100) * c;
  return (
    <div className="inline-flex flex-col items-center gap-1" aria-label={`${label}: ${v}%`}>
      <svg width={size} height={size} role="img">
        <title>{`${label}: ${v}%`}</title>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--surface-subtle)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--brand-700)"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          fontSize="11"
          fontFamily="var(--font-ui)"
          fill="var(--text-primary)"
        >
          {v}%
        </text>
      </svg>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  );
}
