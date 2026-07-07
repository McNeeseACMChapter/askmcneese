import { StatusBadge } from "./StatusBadge";
import { useDarkMode } from "../hooks/useDarkMode";
import type { HealthStatus } from "../types";

interface Props {
  status: HealthStatus;
  version?: string | null;
}

function SunIcon() {
  return (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

export function Header({ status, version }: Props) {
  const { isDark, toggle } = useDarkMode();

  return (
    <header className="bg-[var(--bg-header)] px-4 py-3 text-[var(--text-on-header)]">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-lg font-bold tracking-tight">AskMcNeese</h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggle}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            className="rounded-full p-1.5 text-[var(--text-on-header-muted)] transition hover:bg-white/15 hover:text-[var(--text-on-header)]"
          >
            {isDark ? <SunIcon /> : <MoonIcon />}
          </button>
          <StatusBadge status={status} version={version} />
        </div>
      </div>
      <p className="text-xs text-[var(--text-on-header-muted)]">Your McNeese question assistant</p>
    </header>
  );
}
