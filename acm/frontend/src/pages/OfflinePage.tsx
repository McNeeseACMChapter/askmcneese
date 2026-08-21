import { PageChrome } from "../components/layout/PageChrome";
import { Surface } from "../components/ui/Surface";
import { routeManifest } from "../routes/manifest";

const route = {
  ...routeManifest.find((r) => r.id === "fixtures")!,
  breadcrumb: "Fixtures",
  purpose: "Offline system banner candidate (fixture).",
};

export function OfflinePage() {
  return (
    <PageChrome route={route} title="Offline">
      <div className="status-callout status-callout--warning" role="alert">
        You appear offline. This is a system-wide fixture condition — the only
        appropriate use of a persistent banner.
      </div>
      <Surface level="content" className="p-6">
        <p className="text-sm text-text-secondary">
          Retry is local-only. No network request is made.
        </p>
      </Surface>
    </PageChrome>
  );
}
