import { PageChrome } from "../components/layout/PageChrome";
import { EmptyState } from "../components/ui/EmptyState";
import { Surface } from "../components/ui/Surface";
import { routeManifest } from "../routes/manifest";

const route = {
  ...routeManifest.find((r) => r.id === "fixtures")!,
  breadcrumb: "Fixtures",
  purpose: "Empty queue representation.",
};

export function EmptyStatePage() {
  return (
    <PageChrome route={route} title="Empty state">
      <Surface level="content">
        <EmptyState
          title="Nothing needs attention"
          body="When the queue is clear, keep the editorial voice calm and avoid decorative empty illustrations."
        />
      </Surface>
    </PageChrome>
  );
}
