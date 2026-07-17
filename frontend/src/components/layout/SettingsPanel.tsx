import { RouteEnter } from "../motion/RouteEnter";
import { Panel } from "./SystemStatusPanel";

interface SettingsPanelProps {
  sidebarCollapsed: boolean;
  onSidebarCollapsedChange: (collapsed: boolean) => void;
  onClearHistory: () => void;
}

export function SettingsPanel({ sidebarCollapsed, onSidebarCollapsedChange, onClearHistory }: SettingsPanelProps) {
  return (
    <RouteEnter>
    <Panel title="Settings" description="Preferences are saved only in this browser.">
      <label className="flex items-center justify-between rounded-xl border border-border bg-surface p-4">
        <span><span className="block font-semibold">Collapsed history sidebar</span><span className="text-sm text-text-muted">Use a compact sidebar by default.</span></span>
        <input type="checkbox" checked={sidebarCollapsed} onChange={(event) => onSidebarCollapsedChange(event.target.checked)} className="h-5 w-5 accent-mcneese-blue" />
      </label>
      <div className="rounded-xl border border-border bg-surface p-4">
        <p className="font-semibold">Motion</p>
        <p className="text-sm text-text-muted">Animations follow your device’s reduced-motion preference.</p>
      </div>
      <div className="rounded-xl border border-error/30 bg-surface p-4">
        <p className="font-semibold">Conversation history</p>
        <p className="mb-3 text-sm text-text-muted">Permanently remove conversations stored in this browser.</p>
        <button className="rounded-lg border border-error px-3 py-2 text-sm font-semibold text-error hover:bg-danger-soft" onClick={() => {
          if (window.confirm("Clear all conversation history?")) onClearHistory();
        }}>Clear history</button>
      </div>
    </Panel>
    </RouteEnter>
  );
}
