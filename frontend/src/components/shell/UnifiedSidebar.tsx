import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  ArrowLeftToLine,
  ArrowRightToLine,
  Info,
  KeyRound,
  MessageSquare,
  MessagesSquare,
  Newspaper,
  Plus,
  Search,
  Settings2,
} from "lucide-react";
import type { Conversation } from "../../types";

export type SidebarMode = "ask" | "about" | "updates" | "status" | "other";

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

/** One Lucide family, equal stroke — no one-off filled squares. */
const primary = [
  { to: "/ask", label: "Ask", icon: MessagesSquare, end: true },
  { to: "/about", label: "About", icon: Info, end: false },
  { to: "/updates", label: "Updates", icon: Newspaper, end: true },
  { to: "/status", label: "Status", icon: Activity, end: true },
] as const;

const footer = [
  { to: "/settings", label: "Settings", icon: Settings2 },
  { to: "/feedback", label: "Feedback", icon: MessageSquare },
  { to: "/acm/login", label: "ACM Portal", icon: KeyRound },
] as const;

const ICON = 18;
const STROKE = 1.75;

export function UnifiedSidebar(props: UnifiedSidebarProps) {
  const navigate = useNavigate();
  const reduceMotion = useReducedMotion();
  const iconOnly = props.collapsed && !props.isMobile;

  if (props.isMobile && !props.mobileOpen) return null;

  const panel = (
    <aside
      className={`unified-sidebar liquid-glass flex h-full shrink-0 flex-col${
        iconOnly ? " is-collapsed" : ""
      }${props.isMobile ? " fixed inset-y-0 left-0 z-overlay" : ""}`}
      aria-label="Application"
      data-collapsed={iconOnly ? "true" : "false"}
    >
      <div className="liquid-glass-shine" aria-hidden="true" />
      <div className="liquid-glass-caustic" aria-hidden="true" />

      <div
        className={`relative z-[2] flex h-[4.5rem] shrink-0 items-center ${
          iconOnly ? "justify-center px-2" : "justify-between gap-2 px-4"
        }`}
      >
        {!iconOnly ? (
          <>
            <NavLink
              to="/ask"
              className="min-w-0 truncate font-editorial text-[1.5rem] font-semibold leading-none tracking-tight text-white/95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
              onClick={() => props.isMobile && props.onMobileClose()}
            >
              AskMcNeese
            </NavLink>
            {!props.isMobile && (
              <button
                type="button"
                className="liquid-icon-well relative z-[3] flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center text-white/65 transition hover:text-white/95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                aria-label="Collapse sidebar"
                title="Collapse sidebar"
                aria-expanded={!props.collapsed}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  props.onToggleCollapsed();
                }}
              >
                <ArrowLeftToLine size={ICON} strokeWidth={STROKE} aria-hidden />
              </button>
            )}
          </>
        ) : (
          <button
            type="button"
            className="liquid-icon-well relative z-[3] flex h-11 w-11 cursor-pointer items-center justify-center text-white/70 transition hover:text-white/95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
            aria-label="Expand sidebar"
            title="Expand sidebar"
            aria-expanded={false}
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              props.onToggleCollapsed();
            }}
          >
            <ArrowRightToLine size={ICON} strokeWidth={STROKE} aria-hidden />
          </button>
        )}
      </div>

      <nav className="relative z-[1] flex flex-col gap-2 px-3" aria-label="Primary">
        {primary.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={label}
            aria-label={label}
            onClick={() => props.isMobile && props.onMobileClose()}
            className={({ isActive }) => navRowClass(isActive, iconOnly)}
          >
            {({ isActive }) => (
              <NavRow
                label={label}
                icon={<Icon size={ICON} strokeWidth={STROKE} aria-hidden />}
                isActive={isActive}
                iconOnly={iconOnly}
                reduceMotion={Boolean(reduceMotion)}
                layoutId="primary-liquid-drop"
              />
            )}
          </NavLink>
        ))}
      </nav>

      {!iconOnly && (
        <div className="relative z-[1] mt-6 min-h-0 flex-1 overflow-y-auto px-3 pb-3 scrollbar-thin">
          <ContextualBlock {...props} navigate={navigate} />
        </div>
      )}

      {iconOnly && <div className="relative z-[1] flex-1" />}

      <div className="relative z-[1] mt-auto space-y-1.5 border-t border-white/[0.08] px-3 py-4">
        {footer.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            title={label}
            aria-label={label}
            onClick={() => props.isMobile && props.onMobileClose()}
            className={({ isActive }) => navRowClass(isActive, iconOnly)}
          >
            {({ isActive }) => (
              <NavRow
                label={label}
                icon={<Icon size={ICON} strokeWidth={STROKE} aria-hidden />}
                isActive={isActive}
                iconOnly={iconOnly}
                reduceMotion={Boolean(reduceMotion)}
                layoutId="footer-liquid-drop"
              />
            )}
          </NavLink>
        ))}
        {props.isMobile && (
          <button type="button" className={navRowClass(false, false)} onClick={props.onMobileClose}>
            <span className="px-3 text-sm font-medium text-white/80">Close</span>
          </button>
        )}
      </div>
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

function NavRow({
  label,
  icon,
  isActive,
  iconOnly,
  reduceMotion,
  layoutId,
}: {
  label: string;
  icon: ReactNode;
  isActive: boolean;
  iconOnly: boolean;
  reduceMotion: boolean;
  layoutId?: string;
}) {
  return (
    <span className={`relative flex w-full items-center ${iconOnly ? "justify-center" : "gap-3.5"}`}>
      <AnimatePresence>
        {isActive && layoutId && !reduceMotion && (
          <motion.span
            layoutId={layoutId}
            className="liquid-drop-active absolute inset-0"
            transition={{ type: "spring", stiffness: 380, damping: 36, mass: 0.75 }}
          />
        )}
        {isActive && (!layoutId || reduceMotion) && (
          <span className="liquid-drop-active absolute inset-0" />
        )}
      </AnimatePresence>
      <span className={`liquid-icon-well relative z-[1] ${isActive ? "is-active" : "opacity-80"}`}>{icon}</span>
      {!iconOnly && (
        <span
          className={`relative z-[1] truncate text-[0.9375rem] tracking-[-0.01em] ${
            isActive ? "font-semibold text-white" : "font-medium text-white/70"
          }`}
        >
          {label}
        </span>
      )}
    </span>
  );
}

function ContextualBlock({
  mode,
  conversations,
  activeId,
  onSelectConversation,
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
      <div>
        <p className="mb-3 px-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-white/40">
          Conversations
        </p>
        <button
          type="button"
          onClick={() => {
            onNewChat();
            if (isMobile) onMobileClose();
          }}
          className="liquid-row mb-3 flex min-h-12 w-full items-center gap-3.5 px-2.5 text-[0.9375rem] font-medium text-white/85"
        >
          <span className="liquid-icon-well">
            <Plus size={ICON} strokeWidth={STROKE} aria-hidden />
          </span>
          New conversation
        </button>
        <label className="mb-2 block">
          <span className="sr-only">Search history</span>
          <span className="liquid-search flex items-center gap-2 px-3 py-2">
            <Search size={15} strokeWidth={STROKE} className="shrink-0 text-white/45" aria-hidden />
            <input
              id="history-search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search history"
              className="w-full border-0 bg-transparent text-sm text-white placeholder:text-white/40 focus:outline-none"
            />
          </span>
        </label>
        <ul className="space-y-1">
          {filtered.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => {
                  onSelectConversation(c.id);
                  navigate("/ask");
                  if (isMobile) onMobileClose();
                }}
                className={`liquid-row w-full px-3 py-2.5 text-left ${
                  activeId === c.id ? "is-selected" : ""
                }`}
              >
                <span className="block truncate text-sm font-medium text-white/95">{c.title}</span>
                <span className="mt-0.5 block truncate text-xs text-white/45">{c.preview || "Empty"}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (mode === "about") {
    return (
      <div className="px-2 py-1">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-white/45">About</p>
        <p className="text-sm leading-relaxed text-white/65">
          Team chain of command and what AskMcNeese does — one page.
        </p>
      </div>
    );
  }

  if (mode === "updates") {
    return (
      <div>
        <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-white/45">Updates</p>
        <nav className="flex flex-col gap-1 text-sm" aria-label="Update sections">
          {[
            ["#latest", "Latest"],
            ["#releases", "Releases"],
            ["#development", "Development"],
            ["#limitations", "Known limitations"],
          ].map(([hash, label]) => (
            <a
              key={hash}
              href={`/updates${hash}`}
              className="liquid-row block rounded-[14px] px-3 py-2.5 text-white/70"
              onClick={() => isMobile && onMobileClose()}
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
    );
  }

  return null;
}

function navRowClass(isActive: boolean, iconOnly: boolean) {
  const base = iconOnly
    ? "relative flex h-12 w-12 items-center justify-center rounded-[18px] mx-auto"
    : "relative flex min-h-12 items-center rounded-[18px] px-2.5 py-1";
  return `${base} transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
    isActive ? "text-white" : "text-white/70 hover:text-white/90"
  }`;
}
