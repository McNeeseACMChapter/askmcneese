import { PageChrome } from "../components/layout/PageChrome";
import { Surface } from "../components/ui/Surface";
import { TableSkeleton } from "../components/ui/Skeleton";
import { routeManifest } from "../routes/manifest";

const route = {
  ...routeManifest.find((r) => r.id === "fixtures")!,
  breadcrumb: "Fixtures",
  purpose: "Loading skeleton fixture.",
};

export function LoadingPage() {
  return (
    <PageChrome route={route} title="Loading">
      <Surface level="content">
        <TableSkeleton />
      </Surface>
    </PageChrome>
  );
}
