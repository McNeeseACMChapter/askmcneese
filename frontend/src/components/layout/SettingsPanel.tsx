import { Database, Gauge, History, Search, UserRound } from "lucide-react";
import { useTour } from "../../features/onboarding";
import type { SourceScope } from "../../types";
import { RouteEnter } from "../motion/RouteEnter";
import { Panel } from "./SystemStatusPanel";

interface SettingsPanelProps {
  sidebarCollapsed: boolean;
  onSidebarCollapsedChange: (collapsed: boolean) => void;
  sourceScope: SourceScope;
  onSourceScopeChange: (scope: SourceScope) => void;
  onClearHistory: () => void;
}

export function SettingsPanel({
  sidebarCollapsed,
  onSidebarCollapsedChange,
  sourceScope,
  onSourceScopeChange,
  onClearHistory,
}: SettingsPanelProps) {
  const { phase, replayWalkthrough, guestAlias, guestUsage } = useTour();
  const canReplay = phase === "COMPLETED";

  return (
    <RouteEnter>
      <Panel title="Settings" description="Controls that this beta can honor on this browser.">
        <section className="rounded-2xl border border-border bg-surface p-5">
          <div className="flex items-center gap-4">
            <div
              className="grid h-14 w-14 shrink-0 place-items-center rounded-full text-white shadow-sm"
              style={{
                background:
                  "radial-gradient(circle at 28% 25%, #ffd21c 0 13%, transparent 38%), radial-gradient(circle at 72% 72%, #1677df 0 22%, transparent 52%), linear-gradient(135deg, #073f89, #e7b500)",
              }}
            >
              <UserRound size={24} strokeWidth={1.8} aria-hidden />
            </div>
            <div className="min-w-0">
              <p className="font-semibold">{guestAlias ?? "Guest"}</p>
              <p className="text-sm text-text-muted">This identity returns with this browser.</p>
            </div>
            {guestUsage ? (
              <div className="ml-auto text-right">
                <p className="text-xl font-semibold">{guestUsage.questionsRemaining}</p>
                <p className="text-xs text-text-muted">questions left</p>
              </div>
            ) : null}
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-4 flex items-start gap-3">
            <Search className="mt-0.5 text-mcneese-blue" size={19} aria-hidden />
            <div>
              <p className="font-semibold">Default research mode</p>
              <p className="text-sm text-text-muted">Used for new questions; you can still change it in Ask.</p>
            </div>
          </div>
          <label className="sr-only" htmlFor="default-source-scope">Default research mode</label>
          <select
            id="default-source-scope"
            value={sourceScope}
            onChange={(event) => onSourceScopeChange(event.target.value as SourceScope)}
            className="min-h-11 w-full rounded-xl border border-border bg-surface px-3 text-sm focus:border-mcneese-blue focus:outline-none"
          >
            <option value="adaptive">Adaptive — choose the best path</option>
            <option value="knowledge">Indexed campus sources</option>
            <option value="web">Live web research</option>
          </select>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-4 flex items-start gap-3">
            <Gauge className="mt-0.5 text-mcneese-blue" size={19} aria-hidden />
            <div>
              <p className="font-semibold">Interface</p>
              <p className="text-sm text-text-muted">Layout is saved in this browser.</p>
            </div>
          </div>
          <label className="flex min-h-11 items-center justify-between gap-4">
            <span>
              <span className="block text-sm font-semibold">Compact history sidebar</span>
              <span className="block text-xs text-text-muted">Leave more width for answers.</span>
            </span>
            <input
              type="checkbox"
              checked={sidebarCollapsed}
              onChange={(event) => onSidebarCollapsedChange(event.target.checked)}
              className="h-5 w-5 accent-mcneese-blue"
            />
          </label>
          <p className="mt-3 border-t border-border pt-3 text-xs text-text-muted">
            Motion automatically follows your device’s reduced-motion preference.
          </p>
        </section>

        {canReplay ? (
          <section className="rounded-2xl border border-border bg-surface p-5">
            <div className="flex items-start gap-3">
              <History className="mt-0.5 text-mcneese-blue" size={19} aria-hidden />
              <div className="flex-1">
                <p className="font-semibold">Walkthrough</p>
                <p className="mb-3 text-sm text-text-muted">
                  Replay the product tour without changing your guest identity or allowance.
                </p>
                <button
                  type="button"
                  className="rounded-xl border border-border px-3 py-2 text-sm font-semibold hover:bg-surface-muted"
                  onClick={() => void replayWalkthrough()}
                >
                  Replay walkthrough
                </button>
              </div>
            </div>
          </section>
        ) : null}

        <section className="rounded-2xl border border-error/30 bg-surface p-5">
          <div className="flex items-start gap-3">
            <Database className="mt-0.5 text-text-muted" size={19} aria-hidden />
            <div className="flex-1">
              <p className="font-semibold">Conversation history</p>
              <p className="mb-3 text-sm text-text-muted">
                Conversations are stored locally in this browser. Clearing them does not reset your guest identity.
              </p>
              <button
                className="rounded-xl border border-error px-3 py-2 text-sm font-semibold text-error hover:bg-danger-soft"
                onClick={() => {
                  if (window.confirm("Clear all conversation history from this browser?")) onClearHistory();
                }}
              >
                Clear conversation history
              </button>
            </div>
          </div>
        </section>
      </Panel>
    </RouteEnter>
  );
}
