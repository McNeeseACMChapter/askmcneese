import { useState } from "react";
import { Link } from "react-router-dom";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { fixtureRepo } from "../data/repository";
import { Surface } from "../components/ui/Surface";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/StatusBadge";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../components/toast/ToastProvider";

const route = routeManifest.find((r) => r.id === "notifications")!;

export function NotificationsPage() {
  const state = useFixtureState();
  const { push } = useToast();
  const [pendingId, setPendingId] = useState<string | null>(null);

  const notifications = [...state.notifications].sort(
    (a, b) => Number(b.unread) - Number(a.unread),
  );
  const unreadCount = state.notifications.filter((n) => n.unread).length;

  async function markRead(id: string) {
    setPendingId(id);
    try {
      await fixtureRepo.markNotificationRead(id);
      push({ title: "Marked as read", tone: "success" });
    } catch (error) {
      push({
        title: "Could not update notification",
        description: error instanceof Error ? error.message : "Fixture error.",
        tone: "failure",
      });
    } finally {
      setPendingId(null);
    }
  }

  return (
    <PageChrome route={route} title="Notifications">
      <p className="text-sm text-text-secondary">
        {unreadCount} unread of {notifications.length} total.
      </p>

      {notifications.length === 0 ? (
        <Surface level="content">
          <EmptyState
            title="No notifications"
            body="Chapter alerts and actionable items will appear here."
          />
        </Surface>
      ) : (
        <Surface level="content" className="overflow-hidden">
          <ul className="divide-y divide-[var(--border-subtle)]">
            {notifications.map((n) => (
              <li
                key={n.id}
                className="row-hover flex flex-wrap items-start justify-between gap-3 px-5 py-4"
                style={{ background: n.unread ? "var(--info-soft)" : undefined }}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link to={n.href} className="text-sm font-semibold text-text-primary no-underline">
                      {n.title}
                    </Link>
                    {n.priority === "high" ? (
                      <StatusBadge label="High priority" tone="danger" />
                    ) : null}
                    {n.unread ? <StatusBadge label="Unread" tone="info" /> : null}
                  </div>
                  <p className="mt-1 text-sm text-text-secondary">{n.body}</p>
                  <p className="mt-1 text-xs text-text-muted">{n.at}</p>
                </div>
                {n.unread ? (
                  <Button
                    variant="secondary"
                    disabled={pendingId === n.id}
                    onClick={() => markRead(n.id)}
                  >
                    {pendingId === n.id ? "Marking…" : "Mark read"}
                  </Button>
                ) : (
                  <span className="text-xs text-text-muted">Read</span>
                )}
              </li>
            ))}
          </ul>
        </Surface>
      )}
    </PageChrome>
  );
}
