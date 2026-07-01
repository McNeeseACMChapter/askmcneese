import type { HealthStatus } from "../../types";

interface BadgeProps {
  status: HealthStatus;
  version?: string | null;
}

const statusConfig: Record<HealthStatus, { label: string; dotClass: string }> = {
  checking: { label: "Checking", dotClass: "bg-amber-400 animate-pulse" },
  online: { label: "Online", dotClass: "bg-emerald-400" },
  offline: { label: "Offline", dotClass: "bg-red-400" },
};

export function Badge({ status, version }: BadgeProps) {
  const config = statusConfig[status];
  const label = status === "online" && version ? `${config.label} · v${version}` : config.label;

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm"
      role="status"
      aria-label={`Backend status: ${config.label}`}
    >
      <span className={`h-2 w-2 rounded-full ${config.dotClass}`} aria-hidden="true" />
      {label}
    </span>
  );
}
