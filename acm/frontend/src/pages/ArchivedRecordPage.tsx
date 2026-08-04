import { PageChrome } from "../components/layout/PageChrome";
import { useFixtureState } from "../data/hooks";
import { routeManifest } from "../routes/manifest";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Surface } from "../components/ui/Surface";

const route = routeManifest.find((r) => r.id === "projects")!;

export function ArchivedRecordPage() {
  const state = useFixtureState();
  const project = state.projects.find((p) => p.archived) ?? state.projects[0];

  return (
    <PageChrome route={route} title={project.name}>
      <Surface
        level="content"
        className="p-6"
        style={{ background: "var(--surface-archived)" }}
      >
        <StatusBadge label="Archived" tone="muted" />
        <p className="page-lede mt-3">
          Archived records remain readable. Primary actions are removed in this
          fixture state.
        </p>
        <p className="mt-4 text-sm text-text-secondary">{project.scope}</p>
      </Surface>
    </PageChrome>
  );
}
