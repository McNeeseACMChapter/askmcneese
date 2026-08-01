import { useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  CheckCircle2,
  Database,
  Info,
  Library,
  Newspaper,
  Settings2,
  Workflow,
} from "lucide-react";
import { Sidebar } from "../layout/Sidebar";
import { GlassSidebarShell } from "../layout/GlassSidebarShell";
import type { Conversation } from "../../types";

export type SidebarMode = "ask" | "about" | "updates" | "status" | "other";

interface ContextSidebarProps {
  mode: SidebarMode;
  isOpen: boolean;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onClose: () => void;
  isMobile: boolean;
  conversations: Conversation[];
  activeId: string | null;
  onSelectConversation: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onTogglePin: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
}

const updatesNav = [
  { to: "/updates", label: "Latest", icon: Newspaper },
  { to: "/updates#releases", label: "Releases", icon: CheckCircle2 },
  { to: "/updates#development", label: "Development", icon: Workflow },
  { to: "/updates#limitations", label: "Known limitations", icon: Info },
];

const statusNav = [
  { to: "/status#health", label: "System health", icon: Activity },
  { to: "/status#knowledge", label: "Knowledge base", icon: Database },
  { to: "/status#model", label: "Model availability", icon: Library },
  { to: "/status#config", label: "Current configuration", icon: Settings2 },
];

export function ContextSidebar(props: ContextSidebarProps) {
  if (props.mode === "ask") {
    return (
      <Sidebar
        isOpen={props.isOpen}
        collapsed={props.collapsed && !props.isMobile}
        onToggleCollapsed={props.onToggleCollapsed}
        onClose={props.onClose}
        conversations={props.conversations}
        activeId={props.activeId}
        onSelect={props.onSelectConversation}
        onRename={props.onRename}
        onTogglePin={props.onTogglePin}
        onDelete={props.onDelete}
        isMobile={props.isMobile}
        onNewChat={props.onNewChat}
      />
    );
  }

  const title =
    props.mode === "about"
      ? "About"
      : props.mode === "updates"
        ? "Updates"
        : props.mode === "status"
          ? "Status"
          : "Navigate";

  const collapsed = props.collapsed && !props.isMobile;

  return (
    <AnimatePresence>
      {props.isOpen && (
        <GlassSidebarShell
          key="context-sidebar"
          title={title}
          collapsed={collapsed}
          isMobile={props.isMobile}
          onToggleCollapsed={props.onToggleCollapsed}
          onClose={props.onClose}
          ariaLabel={`${title} navigation`}
        >
          <ContextualNavBody mode={props.mode} collapsed={collapsed} />
        </GlassSidebarShell>
      )}
    </AnimatePresence>
  );
}

function ContextualNavBody({
  mode,
  collapsed,
}: {
  mode: Exclude<SidebarMode, "ask">;
  collapsed: boolean;
}) {
  const location = useLocation();

  return (
    <div key={location.pathname} className="flex h-full flex-col">
      {mode === "about" && !collapsed && (
        <p className="p-4 text-sm leading-relaxed text-text-muted">
          Why AskMcNeese exists, how answers earn trust, and who builds it.
        </p>
      )}
      {mode === "updates" && (
        <nav className="flex flex-col gap-1 p-2" aria-label="Updates sections">
          {updatesNav.map((item) => (
            <ContextHashLink
              key={item.to}
              href={item.to}
              label={item.label}
              Icon={item.icon}
              collapsed={collapsed}
            />
          ))}
        </nav>
      )}
      {mode === "status" && (
        <nav className="flex flex-col gap-1 p-2" aria-label="Status sections">
          {statusNav.map((item) => (
            <ContextHashLink
              key={item.to}
              href={item.to}
              label={item.label}
              Icon={item.icon}
              collapsed={collapsed}
            />
          ))}
        </nav>
      )}
      {mode === "other" && !collapsed && (
        <p className="p-4 text-sm text-text-muted">
          Use the navigation rail or mobile menu to move between product areas.
        </p>
      )}
    </div>
  );
}

function ContextHashLink({
  href,
  label,
  Icon,
  collapsed,
}: {
  href: string;
  label: string;
  Icon: LucideIcon;
  collapsed: boolean;
}) {
  return (
    <a
      href={href}
      title={collapsed ? label : undefined}
      aria-label={label}
      className={[
        "flex min-h-[44px] items-center gap-3 rounded-xl px-3 text-sm transition",
        collapsed ? "justify-center px-0" : "",
        "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
      ].join(" ")}
    >
      <Icon size={17} strokeWidth={1.75} className="flex-shrink-0" aria-hidden />
      {!collapsed && <span>{label}</span>}
    </a>
  );
}
