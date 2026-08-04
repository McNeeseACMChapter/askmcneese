import { PageChrome } from "../components/layout/PageChrome";
import { PermissionNotice } from "../components/ui/PermissionNotice";
import { routeManifest } from "../routes/manifest";

const route = {
  ...routeManifest.find((r) => r.id === "fixtures")!,
  breadcrumb: "System",
  purpose: "Permission-denied state fixture.",
};

export function PermissionDeniedPage() {
  return (
    <PageChrome route={route} title="Permission denied">
      <PermissionNotice
        title="You do not have access"
        body="Unauthorized modules must not appear actionable. This fixture demonstrates a clear denial state."
      />
    </PageChrome>
  );
}
