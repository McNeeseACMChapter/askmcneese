import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { Surface } from "../components/ui/Surface";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { ContentItem } from "../data/types";

const route = routeManifest.find((r) => r.id === "communications")!;

const stageOrder: ContentItem["stage"][] = ["draft", "review", "approved", "scheduled", "published"];

const stageTone: Record<ContentItem["stage"], StatusTone> = {
  draft: "muted",
  review: "warning",
  approved: "success",
  scheduled: "info",
  published: "success",
};

export function CommunicationsPage() {
  const state = useFixtureState();
  const calendar = [...state.content].sort((a, b) =>
    (a.publishAt ?? "9999").localeCompare(b.publishAt ?? "9999"),
  );

  return (
    <PageChrome route={route} title="Communications">
      <div className="board-cols">
        {stageOrder.map((stage) => {
          const items = state.content.filter((c) => c.stage === stage);
          return (
            <div key={stage} className="board-col">
              <h3>
                {stage[0].toUpperCase() + stage.slice(1)} ({items.length})
              </h3>
              <div className="space-y-2">
                {items.length === 0 ? (
                  <p className="text-xs text-text-muted">Nothing here.</p>
                ) : (
                  items.map((item) => (
                    <Surface key={item.id} level="content" className="p-3">
                      <p className="text-sm font-semibold text-text-primary">{item.title}</p>
                      <p className="mt-1 text-xs text-text-muted">
                        {item.channel}
                        {item.publishAt ? ` · ${item.publishAt}` : ""}
                      </p>
                    </Surface>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Surface level="content" className="overflow-hidden">
        <div className="border-b border-[var(--border-subtle)] px-5 py-4">
          <h2>Content calendar</h2>
          <p className="mt-1 text-sm text-text-secondary">Chronological publishing schedule.</p>
        </div>
        <ul className="divide-y divide-[var(--border-subtle)]">
          {calendar.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
              <div>
                <p className="text-sm font-semibold text-text-primary">{item.title}</p>
                <p className="text-xs text-text-muted">{item.channel}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-text-muted">{item.publishAt ?? "Unscheduled"}</span>
                <StatusBadge label={item.stage} tone={stageTone[item.stage]} />
              </div>
            </li>
          ))}
        </ul>
      </Surface>
    </PageChrome>
  );
}
