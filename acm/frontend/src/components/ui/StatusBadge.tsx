import { AlertCircle, Archive, CheckCircle2, Clock3, PauseCircle } from "lucide-react";

const tones = {
  success: { bg: "var(--success-soft)", color: "var(--success)", Icon: CheckCircle2 },
  warning: { bg: "var(--warning-soft)", color: "var(--warning)", Icon: AlertCircle },
  danger: { bg: "var(--danger-soft)", color: "var(--danger)", Icon: PauseCircle },
  info: { bg: "var(--info-soft)", color: "var(--info)", Icon: Clock3 },
  muted: { bg: "var(--surface-subtle)", color: "var(--text-muted)", Icon: Archive },
} as const;

export type StatusTone = keyof typeof tones;

interface StatusBadgeProps {
  label: string;
  tone?: StatusTone;
}

export function StatusBadge({ label, tone = "info" }: StatusBadgeProps) {
  const t = tones[tone];
  const Icon = t.Icon;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
      style={{ background: t.bg, color: t.color, fontFamily: "var(--font-ui)" }}
    >
      <Icon size={14} strokeWidth={1.75} aria-hidden />
      <span>{label}</span>
    </span>
  );
}

export function healthToTone(
  health: string,
): { label: string; tone: StatusTone } {
  switch (health) {
    case "on_track":
      return { label: "On track", tone: "success" };
    case "at_risk":
      return { label: "At risk", tone: "warning" };
    case "blocked":
      return { label: "Blocked", tone: "danger" };
    case "completed":
      return { label: "Completed", tone: "success" };
    case "archived":
      return { label: "Archived", tone: "muted" };
    default:
      return { label: health, tone: "info" };
  }
}
