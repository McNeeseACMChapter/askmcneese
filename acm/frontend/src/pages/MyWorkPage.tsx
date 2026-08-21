import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { usePrototype } from "../state/PrototypeContext";
import { CompactMetric } from "../components/viz/CompactMetric";
import { Sparkline } from "../components/viz/Sparkline";
import { ProgressBar } from "../components/viz/ProgressBar";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { WorkItemState } from "../data/types";

const route = routeManifest.find((r) => r.id === "my-work")!;

type TabId = "now" | "upcoming" | "waiting" | "completed";

const tabs: { id: TabId; label: string; buckets: WorkItemState[] }[] = [
  { id: "now", label: "Now", buckets: ["now", "overdue"] },
  { id: "upcoming", label: "Upcoming", buckets: ["upcoming"] },
  { id: "waiting", label: "Waiting", buckets: ["waiting"] },
  { id: "completed", label: "Completed", buckets: ["completed"] },
];

export function MyWorkPage() {
  const { user, roleId } = usePrototype();
  const state = useFixtureState();
  const [active, setActive] = useState<TabId>("now");

  const mine = useMemo(
    () => state.workItems.filter((w) => w.ownerRole === roleId || w.ownerRole === "any"),
    [state.workItems, roleId],
  );

  const counts = useMemo(() => {
    const map = new Map<TabId, number>();
    tabs.forEach((t) => map.set(t.id, mine.filter((w) => t.buckets.includes(w.bucket)).length));
    return map;
  }, [mine]);

  const activeTab = tabs.find((t) => t.id === active) ?? tabs[0];
  const rows = mine.filter((w) => activeTab.buckets.includes(w.bucket));

  const member = state.members.find((m) => m.name === user.name);
  const workload = member?.engagement ?? [2, 3, 3, 4, 3, 4, 4];

  return (
    <PageChrome route={route} title="My Work">
      <div className="work-split">
        <div className="space-y-4">
          <div className="acm-metric-strip">
            {tabs.map((t) => (
              <CompactMetric key={t.id} label={t.label} value={counts.get(t.id) ?? 0} />
            ))}
          </div>

          <div className="segmented" role="tablist" aria-label="My work view">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={active === t.id}
                data-active={active === t.id ? "true" : "false"}
                onClick={() => setActive(t.id)}
              >
                {t.label} ({counts.get(t.id) ?? 0})
              </button>
            ))}
          </div>

          <Surface level="content" className="overflow-hidden">
            {rows.length === 0 ? (
              <p className="px-5 py-10 text-center text-sm text-text-muted">
                Nothing in {activeTab.label.toLowerCase()} for {user.roleLabel} right now.
              </p>
            ) : (
              <ul className="divide-y divide-[var(--border-subtle)]">
                {rows.map((item) => (
                  <li
                    key={item.id}
                    className="row-hover flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0 flex-1 space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-text-primary">{item.title}</p>
                        <StatusBadge label={item.status} tone={item.statusTone} />
                      </div>
                      <p className="text-sm text-text-secondary">{item.reason}</p>
                      <p className="text-xs text-text-muted">
                        {item.parentLabel} · Due {item.deadline}
                      </p>
                      <div className="max-w-xs">
                        <ProgressBar value={item.progress} label={item.title} />
                      </div>
                    </div>
                    <Link
                      to={item.href}
                      className="acm-btn acm-btn--secondary shrink-0 no-underline"
                    >
                      {item.actionLabel}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Surface>
        </div>

        <div className="space-y-4">
          <Surface level="content" className="p-5">
            <h2 className="text-lg">Workload trend</h2>
            <p className="mt-1 text-sm text-text-secondary">
              {member
                ? `${member.name}'s weekly engagement (fixture).`
                : "Composite chapter workload (fixture)."}
            </p>
            <div className="mt-3">
              <Sparkline
                values={workload}
                label="Workload trend"
                width={220}
                height={64}
                categories={workload.map((_, i) => `W${i + 1}`)}
              />
            </div>
          </Surface>
          <Surface level="content" className="p-5">
            <h2 className="text-lg">Role context</h2>
            <dl className="mt-3 space-y-3 text-sm">
              <div>
                <dt className="text-text-muted">Role</dt>
                <dd className="font-semibold">{user.roleLabel}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Term</dt>
                <dd className="font-semibold">{user.termLabel}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Total assigned</dt>
                <dd className="font-semibold">{mine.length} items</dd>
              </div>
            </dl>
          </Surface>
        </div>
      </div>
    </PageChrome>
  );
}
