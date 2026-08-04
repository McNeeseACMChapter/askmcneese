import { NavLink } from "react-router-dom";
import { LogOut, PanelLeftClose } from "lucide-react";
import {
  navGroupLabels,
  navGroupOrder,
  routeManifest,
  type NavGroup,
} from "../../routes/manifest";
import { usePrototype } from "../../state/PrototypeContext";

const ICON = 18;
const STROKE = 1.75;

export function AcmSidebar() {
  const { user, sidebarCollapsed, toggleSidebar } = usePrototype();

  const workspaceGroups = navGroupOrder.filter((g) => g !== "system");
  const systemRoutes = routeManifest.filter((r) => {
    if (r.navGroup !== "system" || !r.showInSidebar) return false;
    if (r.requiredPermission === "admin" && !user.canViewAdmin) return false;
    if (r.requiredPermission === "audit" && !user.canViewAudit) return false;
    return true;
  });

  return (
    <aside
      className="acm-sidebar"
      data-collapsed={sidebarCollapsed ? "true" : "false"}
      aria-label="ACM Panel navigation"
    >
      <div className="acm-sidebar__brand">
        {sidebarCollapsed ? (
          <button
            type="button"
            className="acm-sidebar__monogram"
            aria-label="Expand navigation"
            title="McNeese ACM"
            onClick={toggleSidebar}
          >
            ACM
          </button>
        ) : (
          <>
            <div className="acm-sidebar__brand-text">
              <NavLink to="/home" className="acm-sidebar__product">
                McNeese ACM
              </NavLink>
              <span className="acm-sidebar__tagline">Internal operations</span>
            </div>
            <button
              type="button"
              className="acm-sidebar__collapse"
              aria-label="Collapse navigation"
              aria-expanded
              onClick={toggleSidebar}
            >
              <PanelLeftClose size={ICON} strokeWidth={STROKE} aria-hidden />
            </button>
          </>
        )}
      </div>

      <nav className="acm-sidebar__nav">
        {workspaceGroups.map((group) => {
          const items = routeManifest.filter(
            (r) => r.navGroup === group && r.showInSidebar,
          );
          if (!items.length) return null;
          return (
            <div key={group}>
              <p className="acm-sidebar__group-label">{navGroupLabels[group as NavGroup]}</p>
              <div className="flex flex-col gap-0.5">
                {items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.end}
                      title={sidebarCollapsed ? item.label : undefined}
                      className={({ isActive }) =>
                        `acm-nav-item${isActive ? " is-active" : ""}`
                      }
                    >
                      <span className="acm-nav-item__icon">
                        <Icon size={ICON} strokeWidth={STROKE} aria-hidden />
                      </span>
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      <div className="acm-sidebar__footer">
        {systemRoutes.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              title={sidebarCollapsed ? item.label : undefined}
              className={({ isActive }) =>
                `acm-nav-item${isActive ? " is-active" : ""}`
              }
            >
              <span className="acm-nav-item__icon">
                <Icon size={ICON} strokeWidth={STROKE} aria-hidden />
              </span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}
        <NavLink
          to="/login"
          title={sidebarCollapsed ? "Sign out" : undefined}
          className="acm-nav-item"
        >
          <span className="acm-nav-item__icon">
            <LogOut size={ICON} strokeWidth={STROKE} aria-hidden />
          </span>
          <span>Sign out</span>
        </NavLink>

        <div className="acm-sidebar__user">
          <span className="acm-sidebar__avatar" aria-hidden>
            {user.initials}
          </span>
          <div className="acm-sidebar__user-meta min-w-0">
            <p className="acm-sidebar__user-name truncate">{user.name}</p>
            <p className="acm-sidebar__user-role truncate">
              {user.roleLabel} · {user.termLabel}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}

export function isNavVisible(
  canViewAdmin: boolean,
  canViewAudit: boolean,
  item: { requiresAdmin?: boolean; requiresAudit?: boolean; requiredPermission?: string },
) {
  if (item.requiresAdmin || item.requiredPermission === "admin") return canViewAdmin;
  if (item.requiresAudit || item.requiredPermission === "audit") return canViewAudit;
  return true;
}
