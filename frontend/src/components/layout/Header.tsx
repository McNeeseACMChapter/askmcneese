import { motion } from "framer-motion";
import { Badge } from "../ui/Badge";
import type { HealthStatus } from "../../types";

interface HeaderProps {
  status: HealthStatus;
  version: string | null;
  onMenuClick: () => void;
  showMenuButton: boolean;
}

export function Header({ status, version, onMenuClick, showMenuButton }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-mcneese-dark/20 bg-gradient-to-r from-mcneese-blue to-mcneese-dark px-4 py-3 shadow-soft">
      <div className="mx-auto flex max-w-chat items-center justify-between">
        <div className="flex items-center gap-3">
          {showMenuButton && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onMenuClick}
              className="rounded-lg p-1.5 text-white/80 hover:bg-white/10 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/30 lg:hidden"
              aria-label="Open menu"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </motion.button>
          )}
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">AskMcNeese</h1>
            <p className="text-xs text-white/60">Your campus assistant</p>
          </div>
        </div>
        <Badge status={status} version={version} />
      </div>
    </header>
  );
}
