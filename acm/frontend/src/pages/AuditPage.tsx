import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { usePrototype } from "../state/PrototypeContext";
import { PermissionNotice } from "../components/ui/PermissionNotice";
import { Surface } from "../components/ui/Surface";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";

const route = routeManifest.find((r) => r.id === "audit")!;

const severityTone: Record<"info" | "warning" | "critical", StatusTone> = {
  info: "info",
  warning: "warning",
  critical: "danger",
};

export function AuditPage() {
  const { user } = usePrototype();
  const state = useFixtureState();

  if (!user.canViewAudit) {
    return (
      <PageChrome route={route} title="Audit">
        <PermissionNotice />
      </PageChrome>
    );
  }

  const events = [...state.audit].sort((a, b) => b.at.localeCompare(a.at));

  return (
    <PageChrome route={route} title="Audit">
      <Surface level="content" className="overflow-hidden">
        <div className="dense-row font-semibold text-text-muted">
          <span>Timestamp</span>
          <span>Actor</span>
          <span>Action / resource</span>
          <span>Before → after</span>
          <span>Severity</span>
        </div>
        {events.map((e) => (
          <div key={e.id} className="dense-row">
            <span className="text-text-muted">
              {new Date(e.at).toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              })}
            </span>
            <span className="font-semibold text-text-primary" title={e.actor}>
              {e.actorInitials}
            </span>
            <span>
              <strong className="text-text-primary">{e.action}</strong>{" "}
              <span className="text-text-secondary">{e.resource}</span>
              {e.reason ? <span className="block text-xs text-text-muted">{e.reason}</span> : null}
            </span>
            <span className="text-text-muted">
              {e.before ?? "—"} → {e.after ?? "—"}
            </span>
            <span>
              <StatusBadge label={e.severity} tone={severityTone[e.severity]} />
            </span>
          </div>
        ))}
      </Surface>
    </PageChrome>
  );
}
