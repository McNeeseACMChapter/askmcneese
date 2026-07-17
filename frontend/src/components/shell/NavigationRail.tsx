import { NavLink } from "react-router-dom";
import {
  Activity,
  Info,
  MessageCircleQuestion,
  MessageSquareText,
  Newspaper,
  PanelLeftClose,
  PanelLeftOpen,
  Settings2,
} from "lucide-react";

interface NavigationRailProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const primary = [
  { to: "/ask", label: "Ask", icon: MessageCircleQuestion },
  { to: "/about", label: "About", icon: Info, end: false },
  { to: "/updates", label: "Updates", icon: Newspaper },
  { to: "/status", label: "Status", icon: Activity },
] as const;

const secondary = [
  { to: "/settings", label: "Settings", icon: Settings2 },
  { to: "/feedback", label: "Feedback", icon: MessageSquareText },
] as const;

const iconProps = { size: 20, strokeWidth: 1.75, absoluteStrokeWidth: true as const };

export function NavigationRail({ sidebarOpen, onToggleSidebar }: NavigationRailProps) {
  return (
    <nav
      className="glass-navigation hidden h-full w-nav-rail shrink-0 flex-col items-center border-r border-[var(--glass-border)] py-3 md:flex"
      aria-label="Primary"
    >
      <div className="flex flex-1 flex-col items-center gap-2">
        {primary.map(({ to, label, icon: Icon, ...rest }) => (
          <NavLink
            key={to}
            to={to}
            end={"end" in rest ? rest.end : true}
            title={label}
            aria-label={label}
            className={({ isActive }) =>
              `flex h-11 w-11 items-center justify-center rounded-xl transition duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
                isActive
                  ? "bg-brand-700 text-white shadow-soft [&_svg]:stroke-[2]"
                  : "text-text-secondary hover:bg-surface-hover hover:text-brand-700"
              }`
            }
          >
            <Icon {...iconProps} aria-hidden />
          </NavLink>
        ))}
      </div>

      <div className="flex flex-col items-center gap-2">
        {secondary.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            title={label}
            aria-label={label}
            className={({ isActive }) =>
              `flex h-11 w-11 items-center justify-center rounded-xl transition duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
                isActive
                  ? "bg-brand-700 text-white shadow-soft [&_svg]:stroke-[2]"
                  : "text-text-secondary hover:bg-surface-hover hover:text-brand-700"
              }`
            }
          >
            <Icon {...iconProps} aria-hidden />
          </NavLink>
        ))}
        <button
          type="button"
          title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          onClick={onToggleSidebar}
          className="flex h-11 w-11 items-center justify-center rounded-xl text-text-secondary transition duration-fast hover:bg-surface-hover hover:text-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
        >
          {sidebarOpen ? (
            <PanelLeftClose {...iconProps} aria-hidden />
          ) : (
            <PanelLeftOpen {...iconProps} aria-hidden />
          )}
        </button>
      </div>
    </nav>
  );
}
