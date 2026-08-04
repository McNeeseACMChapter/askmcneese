import { Outlet, useLocation } from "react-router-dom";
import { findRouteByPath } from "../../routes/manifest";
import { AcmMobileNavigation } from "./AcmMobileNavigation";
import { AcmRouteHeader } from "./AcmRouteHeader";
import { AcmSidebar } from "./AcmSidebar";

export function AcmAppShell() {
  const { pathname } = useLocation();
  const route = findRouteByPath(pathname);

  return (
    <div className="acm-shell">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <AcmSidebar />
      <AcmMobileNavigation />
      <div className="acm-shell__main">
        <AcmRouteHeader
          breadcrumb={route?.breadcrumb}
          primaryActionLabel={route?.primaryAction?.label}
        />
        <div id="main-content" className="acm-shell__content" tabIndex={-1}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
