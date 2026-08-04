interface CompactMetricProps {
  label: string;
  value: string | number;
  hint?: string;
  delta?: string;
  deltaTone?: "up" | "down" | "flat";
}

export function CompactMetric({
  label,
  value,
  hint,
  delta,
  deltaTone = "flat",
}: CompactMetricProps) {
  const deltaColor =
    deltaTone === "up"
      ? "var(--success)"
      : deltaTone === "down"
        ? "var(--danger)"
        : "var(--text-muted)";
  return (
    <div className="acm-metric">
      <p className="acm-metric__label">{label}</p>
      <p className="acm-metric__value">{value}</p>
      {delta ? (
        <p className="acm-metric__delta" style={{ color: deltaColor }}>
          {delta}
        </p>
      ) : null}
      {hint ? <p className="acm-metric__hint">{hint}</p> : null}
    </div>
  );
}
