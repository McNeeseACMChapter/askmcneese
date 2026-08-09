import { useState, type CSSProperties } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import {
  Activity,
  CalendarDays,
  Info,
  MessageSquare,
  MessagesSquare,
  Newspaper,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Settings2,
} from "lucide-react";
import type { Conversation } from "../../types";
import { useTour } from "../../features/onboarding";
import { BrandLogo } from "../brand/BrandLogo";
import { ConversationMenu } from "../layout/ConversationMenu";

const TOUR_IDS: Record<string, string> = {
  "/ask": "ask",
  "/class-planner": "class-planner",
  "/about": "about",
  "/updates": "updates",
  "/status": "usage",
  "/settings": "settings",
  "/feedback": "feedback",
};

export type SidebarMode = "ask" | "planner" | "about" | "updates" | "status" | "other";

interface UnifiedSidebarProps {
  mode: SidebarMode;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  isMobile: boolean;
  mobileOpen: boolean;
  onMobileClose: () => void;
  conversations: Conversation[];
  activeId: string | null;
  onSelectConversation: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onTogglePin: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
}

const primary = [
  { to: "/ask", label: "Ask", icon: MessagesSquare, end: true },
  { to: "/class-planner", label: "Class Planner", icon: CalendarDays, end: true },
  { to: "/about", label: "About", icon: Info, end: false },
  { to: "/updates", label: "Updates", icon: Newspaper, end: true },
  { to: "/status", label: "Usage", icon: Activity, end: true },
] as const;

const footer = [
  { to: "/settings", label: "Settings", icon: Settings2 },
  { to: "/feedback", label: "Feedback", icon: MessageSquare },
] as const;

const NAV_ICON = 20;
const COMPACT_ICON = 19;
const SEARCH_ICON = 17;
const STROKE = 1.7;
const STROKE_ACTIVE = 2;
const STROKE_ACTION = 1.8;

export function UnifiedSidebar(props: UnifiedSidebarProps) {
  const navigate = useNavigate();
  const reduceMotion = Boolean(useReducedMotion());
  const { notifyTargetActivated } = useTour();
  const iconOnly = props.collapsed && !props.isMobile;

  if (props.isMobile && !props.mobileOpen) return null;

  const collapseLabel = iconOnly ? "Expand navigation" : "Collapse navigation";

  const panel = (
    <aside
      className={`appSidebar${iconOnly ? " is-collapsed" : ""}${
        props.isMobile ? " fixed inset-y-0 left-0 z-overlay" : ""
      }`}
      aria-label="AskMcNeese navigation"
      data-collapsed={iconOnly ? "true" : "false"}
      data-reduced-motion={reduceMotion ? "true" : "false"}
      style={
        reduceMotion
          ? ({ transition: "none" } as CSSProperties)
          : undefined
      }
    >
      <header className="appSidebarHeader">
        {!iconOnly ? (
          <>
            <NavLink
              to="/ask"
              className="appSidebarBrand"
              data-tour-id="logo"
              onClick={() => {
                notifyTargetActivated("logo");
                props.isMobile && props.onMobileClose();
              }}
            >
              <BrandLogo variant="horizontal" decorative eager className="appSidebarBrandLogo" />
              <span className="sr-only">AskMcNeese</span>
            </NavLink>
            {!props.isMobile && (
              <button
                type="button"
                className="appSidebarCollapse"
                aria-label={collapseLabel}
                title={collapseLabel}
                aria-expanded={!props.collapsed}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  props.onToggleCollapsed();
                }}
              >
                <PanelLeftClose size={COMPACT_ICON} strokeWidth={1.75} aria-hidden />
              </button>
            )}
          </>
        ) : (
          <button
            type="button"
            className="appSidebarCollapse"
            aria-label={collapseLabel}
            title={collapseLabel}
            aria-expanded={false}
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              props.onToggleCollapsed();
            }}
          >
            <PanelLeftOpen size={COMPACT_ICON} strokeWidth={1.75} aria-hidden />
          </button>
        )}
      </header>

      <nav className="appSidebarPrimaryNav" aria-label="Primary">
        {primary.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={label}
            aria-label={label}
            data-tour-id={TOUR_IDS[to]}
            onClick={() => {
              const tourId = TOUR_IDS[to];
              if (tourId) notifyTargetActivated(tourId);
              props.isMobile && props.onMobileClose();
            }}
            className={({ isActive }) =>
              `appSidebarNavItem${isActive ? " is-active" : ""}`
            }
          >
            {({ isActive }) => (
              <>
                <span className="appSidebarNavIcon">
                  <Icon
                    size={NAV_ICON}
                    strokeWidth={isActive ? STROKE_ACTIVE : STROKE}
                    aria-hidden
                  />
                </span>
                <span className="appSidebarNavLabel">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {iconOnly ? (
        <div className="appSidebarCollapsedActions">
          <button
            type="button"
            className="appSidebarNewChat"
            title="New conversation"
            aria-label="New conversation"
            onClick={() => {
              props.onNewChat();
            }}
          >
            <span className="appSidebarNewChatIcon">
              <Plus size={COMPACT_ICON} strokeWidth={STROKE_ACTION} aria-hidden />
            </span>
            <span className="appSidebarNewChatLabel">New conversation</span>
          </button>
        </div>
      ) : (
        <section
          className="appSidebarConversations"
          aria-label={props.mode === "ask" ? "Conversations" : "Page context"}
          data-tour-id="conversations"
        >
          <ContextualBlock {...props} navigate={navigate} />
        </section>
      )}

      <footer className="appSidebarUtilities">
        {footer.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            title={label}
            aria-label={label}
            data-tour-id={TOUR_IDS[to]}
            onClick={() => {
              const tourId = TOUR_IDS[to];
              if (tourId) notifyTargetActivated(tourId);
              props.isMobile && props.onMobileClose();
            }}
            className={({ isActive }) =>
              `appSidebarUtilityItem${isActive ? " is-active" : ""}`
            }
          >
            <span className="appSidebarUtilityIcon">
              <Icon size={COMPACT_ICON} strokeWidth={STROKE} aria-hidden />
            </span>
            <span className="appSidebarUtilityLabel">{label}</span>
          </NavLink>
        ))}
        {props.isMobile && (
          <button
            type="button"
            className="appSidebarCloseMobile"
            onClick={props.onMobileClose}
          >
            Close
          </button>
        )}
      </footer>
    </aside>
  );

  if (!props.isMobile) return panel;

  return (
    <div className="fixed inset-0 z-overlay md:hidden">
      <button
        type="button"
        className="absolute inset-0 bg-black/30 backdrop-blur-[6px]"
        aria-label="Close navigation"
        onClick={props.onMobileClose}
      />
      {panel}
    </div>
  );
}

function ContextualBlock({
  mode,
  conversations,
  activeId,
  onSelectConversation,
  onRename,
  onTogglePin,
  onDelete,
  onNewChat,
  isMobile,
  onMobileClose,
  navigate,
}: UnifiedSidebarProps & { navigate: ReturnType<typeof useNavigate> }) {
  const [search, setSearch] = useState("");

  if (mode === "ask") {
    const filtered = conversations.filter((c) =>
      `${c.title} ${c.preview}`.toLowerCase().includes(search.toLowerCase()),
    );
    return (
      <>
        <p className="appSidebarSectionLabel">Conversations</p>
        <button
          type="button"
          className="appSidebarNewChat"
          onClick={() => {
            onNewChat();
            if (isMobile) onMobileClose();
          }}
        >
          <span className="appSidebarNewChatIcon">
            <Plus size={COMPACT_ICON} strokeWidth={STROKE_ACTION} aria-hidden />
          </span>
          <span className="appSidebarNewChatLabel">New conversation</span>
        </button>
        <label className="appSidebarSearch">
          <span className="sr-only">Search history</span>
          <Search
            size={SEARCH_ICON}
            strokeWidth={STROKE}
            className="appSidebarSearchIcon"
            aria-hidden
          />
          <input
            id="history-search"
            className="appSidebarSearchInput"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search history"
          />
        </label>
        <ul className="appSidebarHistory">
          {filtered.map((conversation) => {
            const selected = activeId === conversation.id;
            return (
              <li
                key={conversation.id}
                className={`appSidebarHistoryItem group${selected ? " is-selected" : ""}`}
              >
                <button
                  type="button"
                  className="appSidebarHistoryButton"
                  aria-current={selected ? "true" : undefined}
                  onClick={() => {
                    onSelectConversation(conversation.id);
                    navigate("/ask");
                    if (isMobile) onMobileClose();
                  }}
                >
                  <span className="appSidebarHistoryTitle">{conversation.title}</span>
                  <span className="appSidebarHistoryPreview">
                    {conversation.preview || "Empty"}
                  </span>
                </button>
                <div className="appSidebarHistoryMenu">
                  <ConversationMenu
                    conversation={conversation}
                    onRename={() => {
                      const next = window.prompt(
                        "Rename conversation",
                        conversation.title,
                      );
                      if (next?.trim()) onRename(conversation.id, next.trim());
                    }}
                    onTogglePin={() => onTogglePin(conversation.id)}
                    onDelete={() => onDelete(conversation.id)}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      </>
    );
  }

  if (mode === "about") {
    return (
      <>
        <p className="appSidebarSectionLabel">About</p>
        <p className="appSidebarContextNote">
          Why AskMcNeese exists, how answers earn trust, and who builds it.
        </p>
      </>
    );
  }

  if (mode === "updates") {
    return (
      <>
        <p className="appSidebarSectionLabel">Updates</p>
        <nav className="appSidebarContextLinks" aria-label="Update sections">
          {(
            [
              ["#latest", "Latest"],
              ["#releases", "Releases"],
              ["#development", "Development"],
              ["#limitations", "Known limitations"],
            ] as const
          ).map(([hash, label]) => (
            <a
              key={hash}
              href={`/updates${hash}`}
              className="appSidebarContextLink"
              onClick={() => isMobile && onMobileClose()}
            >
              {label}
            </a>
          ))}
        </nav>
      </>
    );
  }

  return null;
}
