import { Menu } from "lucide-react";
import type { HealthStatus } from "../../types";

interface RouteHeaderProps {
  status: HealthStatus;
  version: string | null;
  title: string;
  subtitle?: string;
  onMenuClick: () => void;
  showMenuButton: boolean;
}

export function RouteHeader({
  status,
  version,
  title,
  subtitle,
  onMenuClick,
  showMenuButton,
}: RouteHeaderProps) {
  return (
    <header className="glass-navigation sticky top-0 z-header flex h-header items-center justify-between border-b border-[var(--glass-border)] px-[var(--page-gutter)]">
      <div className="flex min-w-0 items-center gap-3">
        {showMenuButton && (
          <button
            type="button"
            onClick={onMenuClick}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-text-secondary transition hover:bg-surface-hover hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus lg:hidden"
            aria-label="Open sidebar"
          >
            <Menu size={20} strokeWidth={1.75} aria-hidden />
          </button>
        )}
        <div className="min-w-0">
          <h1 className="truncate font-editorial text-lg font-semibold text-text-primary md:text-xl">
            {title}
          </h1>
          {subtitle && (
            <p className="hidden truncate text-xs text-text-muted sm:block">{subtitle}</p>
          )}
        </div>
      </div>
      <StatusIndicator status={status} version={version} />
    </header>
  );
}

function StatusIndicator({ status, version }: { status: HealthStatus; version: string | null }) {
  const config: Record<HealthStatus, { color: string; pulse: boolean; label: string }> = {
    checking: { color: "bg-warning", pulse: true, label: "Connecting…" },
    online: { color: "bg-success", pulse: false, label: version ? `v${version}` : "Online" },
    offline: { color: "bg-error", pulse: false, label: "Offline" },
  };
  const { color, pulse, label } = config[status];
  return (
    <div
      className="flex items-center gap-1.5 text-xs text-text-muted"
      role="status"
      aria-label={`Backend status: ${label}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${color} ${pulse ? "animate-pulse" : ""}`} />
      <span>{label}</span>
    </div>
  );
}
