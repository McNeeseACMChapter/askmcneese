import type { ReactNode } from "react";
import { widthClass, type AcmRouteDefinition } from "../../routes/manifest";
import { RouteEnter } from "../motion/RouteEnter";
import { DataModeIndicator } from "./DataModeIndicator";

interface PageChromeProps {
  route: AcmRouteDefinition;
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}

/** One H1 in content; header carries breadcrumb only via shell. */
export function PageChrome({ route, title, children, actions }: PageChromeProps) {
  return (
    <RouteEnter className={widthClass(route.width)}>
      <div className="page-chrome">
        <div className="page-chrome__head">
          <div className="min-w-0">
            <h1>{title}</h1>
            <p className="page-lede">{route.purpose}</p>
          </div>
          {actions ? <div className="page-chrome__actions">{actions}</div> : null}
        </div>
        <DataModeIndicator route={route} />
        <div className="page-chrome__body">{children}</div>
      </div>
    </RouteEnter>
  );
}
