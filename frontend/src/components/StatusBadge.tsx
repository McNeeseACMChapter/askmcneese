import type { HealthStatus } from "../types";

const LABELS: Record<HealthStatus, string> = {
  checking: "Checking",
  online: "Online",
  offline: "Offline",
};

const DOT: Record<HealthStatus, string> = {
  checking: "bg-amber-400 animate-pulse",
  online: "bg-green-400",
  offline: "bg-red-400",
};

interface Props {
  status: HealthStatus;
  version?: string | null;
}

export function StatusBadge({ status, version }: Props) {
  const label = status === "online" && version ? `${LABELS[status]} · v${version}` : LABELS[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-xs font-medium text-white"
      title={`Backend status: ${LABELS[status]}`}
    >
      <span className={`h-2 w-2 rounded-full ${DOT[status]}`} />
      {label}
    </span>
  );
}
