import { motion } from "framer-motion";
import type { HealthStatus } from "../../types";
import { BrandLogo } from "../brand/BrandLogo";

interface HeaderProps {
  status: HealthStatus;
  version: string | null;
  onMenuClick: () => void;
  showMenuButton: boolean;
  title?: string;
}

export function Header({ status, version, onMenuClick, showMenuButton, title = "AskMcNeese" }: HeaderProps) {
  return (
    <header className="sticky top-0 z-header h-header flex items-center justify-between border-b border-border bg-surface/80 backdrop-blur-md px-4 md:px-6">
      <div className="flex items-center gap-3">
        {showMenuButton && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onMenuClick}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-text-secondary hover:bg-bg-secondary hover:text-text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-mcneese-blue lg:hidden"
            aria-label="Open menu"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </motion.button>
        )}
        
        <div className="flex items-center gap-2.5">
          <BrandLogo variant="mark" decorative eager className="legacyHeaderMark" />
          <div>
            <span className="font-editorial text-lg font-semibold text-text-primary">{title}</span>
            <p className="hidden text-[11px] text-text-muted sm:block">McNeese information assistant</p>
          </div>
        </div>
      </div>

      <StatusIndicator status={status} version={version} />
    </header>
  );
}

function StatusIndicator({ status, version }: { status: HealthStatus; version: string | null }) {
  const config: Record<HealthStatus, { color: string; pulse: boolean; label: string }> = {
    checking: { color: "bg-warning", pulse: true, label: "Connecting..." },
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
      <span className={`h-1.5 w-1.5 rounded-full ${color} ${pulse ? 'animate-pulse' : ''}`} />
      <span>{label}</span>
    </div>
  );
}
