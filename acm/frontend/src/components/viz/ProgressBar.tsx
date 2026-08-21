interface ProgressBarProps {
  value: number;
  label: string;
  showValue?: boolean;
}

export function ProgressBar({ value, label, showValue = true }: ProgressBarProps) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className="acm-progress" aria-label={`${label}: ${v}%`}>
      <div className="acm-progress__track">
        <div className="acm-progress__fill" style={{ width: `${v}%` }} />
      </div>
      {showValue ? <span className="acm-progress__value">{v}%</span> : null}
    </div>
  );
}
